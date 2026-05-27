from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image

from app.fashion_advisor.knowledge_base import FashionKnowledgeBase, RetrievedDocument
from app.fashion_advisor.llm_client import AdvisorLLMClient
from app.fashion_advisor.prompts import build_style_plan_prompts
from app.services.ai_service import AIService
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentContext:
    image_path: str
    user_id: str | None
    occasion: str
    weather: str
    temperature: str
    notes: str
    prefer_wardrobe: bool
    city: str = ""
    client_ip: str = ""


@dataclass(slots=True)
class ToolResult:
    tool_name: str
    status: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)


class OutfitAdvisorAgent:
    """Outfit planning agent with optional LangGraph orchestration."""

    def __init__(self, llm_client: AdvisorLLMClient, knowledge_base: FashionKnowledgeBase) -> None:
        self.llm_client = llm_client
        self.knowledge_base = knowledge_base
        self.ai_service = AIService()

    def run(
        self,
        context: AgentContext,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        if self._langgraph_requested():
            try:
                return self._run_with_langgraph(context, progress_callback=progress_callback)
            except Exception:
                logger.exception("LangGraph workflow failed; falling back to sequential execution")
        return self._run_sequential(context, progress_callback=progress_callback)

    def _run_sequential(
        self,
        context: AgentContext,
        *,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        workflow = self._build_workflow_descriptor(engine="sequential")
        self._emit_progress(
            progress_callback,
            step="workflow_ready",
            label="初始化流程",
            detail="已准备顺序执行的 Agent 工作流。",
            progress=5,
            workflow=workflow,
        )

        analysis_tool = self._tool_analyze_image(context.image_path)
        trace.append(self._to_trace(analysis_tool))
        self._emit_progress(
            progress_callback,
            step=analysis_tool.tool_name,
            label="分析图片",
            detail=analysis_tool.detail,
            progress=18,
            workflow=workflow,
        )

        weather_tool = self._tool_fetch_weather(context)
        trace.append(self._to_trace(weather_tool))
        weather_context = weather_tool.data
        self._emit_progress(
            progress_callback,
            step=weather_tool.tool_name,
            label="获取天气",
            detail=weather_tool.detail,
            progress=36,
            workflow=workflow,
        )

        if not context.weather and weather_context.get("weather"):
            context = AgentContext(
                image_path=context.image_path,
                user_id=context.user_id,
                occasion=context.occasion,
                weather=weather_context.get("weather", ""),
                temperature=str(weather_context.get("temperature", "")),
                notes=context.notes,
                prefer_wardrobe=context.prefer_wardrobe,
                city=context.city,
                client_ip=context.client_ip,
            )

        retrieval_query = self._build_retrieval_query(analysis_tool.data, context)
        knowledge_tool = self._tool_retrieve_knowledge(retrieval_query)
        trace.append(self._to_trace(knowledge_tool))
        self._emit_progress(
            progress_callback,
            step=knowledge_tool.tool_name,
            label="检索知识库",
            detail=knowledge_tool.detail,
            progress=58,
            workflow=workflow,
        )

        memory_tool = self._tool_retrieve_memory(context, retrieval_query)
        trace.append(self._to_trace(memory_tool))
        self._emit_progress(
            progress_callback,
            step=memory_tool.tool_name,
            label="检索衣橱记忆",
            detail=memory_tool.detail,
            progress=76,
            workflow=workflow,
        )

        plan_tool = self._tool_generate_plan(
            analysis=analysis_tool.data,
            knowledge_docs=knowledge_tool.data.get("docs", []),
            memory_docs=memory_tool.data.get("docs", []),
            weather_context=weather_context,
            context=context,
        )
        trace.append(self._to_trace(plan_tool))
        self._emit_progress(
            progress_callback,
            step=plan_tool.tool_name,
            label="生成方案",
            detail=plan_tool.detail,
            progress=100,
            workflow=workflow,
        )

        return self._build_result_payload(
            analysis=analysis_tool.data,
            weather_context=weather_context,
            knowledge_docs=knowledge_tool.data.get("docs", []),
            memory_docs=memory_tool.data.get("docs", []),
            recommendation=plan_tool.data,
            trace=trace,
            workflow=workflow,
        )

    def _run_with_langgraph(
        self,
        context: AgentContext,
        *,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        try:
            from langgraph.graph import END, StateGraph
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("langgraph is unavailable") from exc

        workflow = self._build_workflow_descriptor(engine="langgraph")
        self._emit_progress(
            progress_callback,
            step="workflow_ready",
            label="初始化流程",
            detail="已切换到 LangGraph 工作流。",
            progress=5,
            workflow=workflow,
        )

        state: dict[str, Any] = {"context": context, "trace": []}

        def analyze_node(current: dict[str, Any]) -> dict[str, Any]:
            tool = self._tool_analyze_image(current["context"].image_path)
            trace = list(current.get("trace", []))
            trace.append(self._to_trace(tool))
            self._emit_progress(
                progress_callback,
                step=tool.tool_name,
                label="分析图片",
                detail=tool.detail,
                progress=18,
                workflow=workflow,
            )
            return {"analysis_tool": tool, "trace": trace}

        def weather_node(current: dict[str, Any]) -> dict[str, Any]:
            working_context: AgentContext = current["context"]
            tool = self._tool_fetch_weather(working_context)
            weather_context = tool.data
            if not working_context.weather and weather_context.get("weather"):
                working_context = AgentContext(
                    image_path=working_context.image_path,
                    user_id=working_context.user_id,
                    occasion=working_context.occasion,
                    weather=weather_context.get("weather", ""),
                    temperature=str(weather_context.get("temperature", "")),
                    notes=working_context.notes,
                    prefer_wardrobe=working_context.prefer_wardrobe,
                    city=working_context.city,
                    client_ip=working_context.client_ip,
                )
            trace = list(current.get("trace", []))
            trace.append(self._to_trace(tool))
            self._emit_progress(
                progress_callback,
                step=tool.tool_name,
                label="获取天气",
                detail=tool.detail,
                progress=36,
                workflow=workflow,
            )
            return {"context": working_context, "weather_tool": tool, "trace": trace}

        def knowledge_node(current: dict[str, Any]) -> dict[str, Any]:
            query = self._build_retrieval_query(current["analysis_tool"].data, current["context"])
            tool = self._tool_retrieve_knowledge(query)
            trace = list(current.get("trace", []))
            trace.append(self._to_trace(tool))
            self._emit_progress(
                progress_callback,
                step=tool.tool_name,
                label="检索知识库",
                detail=tool.detail,
                progress=58,
                workflow=workflow,
            )
            return {"retrieval_query": query, "knowledge_tool": tool, "trace": trace}

        def memory_node(current: dict[str, Any]) -> dict[str, Any]:
            tool = self._tool_retrieve_memory(current["context"], current["retrieval_query"])
            trace = list(current.get("trace", []))
            trace.append(self._to_trace(tool))
            self._emit_progress(
                progress_callback,
                step=tool.tool_name,
                label="检索衣橱记忆",
                detail=tool.detail,
                progress=76,
                workflow=workflow,
            )
            return {"memory_tool": tool, "trace": trace}

        def plan_node(current: dict[str, Any]) -> dict[str, Any]:
            tool = self._tool_generate_plan(
                analysis=current["analysis_tool"].data,
                knowledge_docs=current["knowledge_tool"].data.get("docs", []),
                memory_docs=current["memory_tool"].data.get("docs", []),
                weather_context=current["weather_tool"].data,
                context=current["context"],
            )
            trace = list(current.get("trace", []))
            trace.append(self._to_trace(tool))
            self._emit_progress(
                progress_callback,
                step=tool.tool_name,
                label="生成方案",
                detail=tool.detail,
                progress=100,
                workflow=workflow,
            )
            return {"plan_tool": tool, "trace": trace}

        graph = StateGraph(dict)
        graph.add_node("analyze_image", analyze_node)
        graph.add_node("fetch_weather", weather_node)
        graph.add_node("retrieve_knowledge", knowledge_node)
        graph.add_node("retrieve_memory", memory_node)
        graph.add_node("generate_plan", plan_node)
        graph.set_entry_point("analyze_image")
        graph.add_edge("analyze_image", "fetch_weather")
        graph.add_edge("fetch_weather", "retrieve_knowledge")
        graph.add_edge("retrieve_knowledge", "retrieve_memory")
        graph.add_edge("retrieve_memory", "generate_plan")
        graph.add_edge("generate_plan", END)
        final_state = graph.compile().invoke(state)

        return self._build_result_payload(
            analysis=final_state["analysis_tool"].data,
            weather_context=final_state["weather_tool"].data,
            knowledge_docs=final_state["knowledge_tool"].data.get("docs", []),
            memory_docs=final_state["memory_tool"].data.get("docs", []),
            recommendation=final_state["plan_tool"].data,
            trace=final_state.get("trace", []),
            workflow=workflow,
        )

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _tool_analyze_image(self, image_path: str) -> ToolResult:
        try:
            rich_analysis = self.ai_service.analyze_image_attributes(image_path)
        except Exception:
            logger.exception("rich image analysis failed")
            rich_analysis = {}

        caption = rich_analysis.get("caption", "") or self._safe_generate_caption(image_path)
        color_hint = rich_analysis.get("color", "")
        style_hint = rich_analysis.get("style", "")
        category_hint = rich_analysis.get("category", "")
        material_hint = rich_analysis.get("material", "")
        additional_tags = list(rich_analysis.get("additional_tags", []))

        try:
            image = Image.open(image_path).convert("RGB")
            dominant_color = self._extract_dominant_color(image)
        except Exception:
            dominant_color = color_hint or "未知"

        item_type = category_hint if category_hint and category_hint != "未分类" else self._infer_item_type(caption, image_path)
        style_keywords = self._build_style_keywords(style_hint, caption, dominant_color, item_type, additional_tags)
        material_hints = [material_hint] if material_hint and material_hint != "未知材质" else self._infer_material_hints(caption)
        palette = self._describe_palette(dominant_color)
        primary_style = style_keywords[0] if style_keywords else "日常"
        secondary_style = style_keywords[1] if len(style_keywords) > 1 else primary_style
        summary = (
            f"这是一件偏{palette}、以{item_type}为主的单品，整体更接近{primary_style}风格，"
            f"适合围绕“{primary_style} + {secondary_style}”延展搭配。"
        )

        analysis = {
            "caption": caption,
            "item_type": item_type,
            "dominant_color": dominant_color,
            "palette": palette,
            "style_keywords": style_keywords,
            "material_hints": material_hints,
            "additional_tags": additional_tags,
            "summary": summary,
        }
        detail = f"完成图片分析：{item_type} / {dominant_color} / {primary_style}"
        return ToolResult("analyze_image", "completed", detail, analysis)

    def _tool_fetch_weather(self, context: AgentContext) -> ToolResult:
        user_weather = context.weather.strip()
        user_temp = context.temperature.strip()

        if user_weather and user_temp:
            try:
                numeric = float(user_temp)
            except ValueError:
                numeric = None
            weather_data = {
                "weather": user_weather,
                "temperature_text": f"{user_temp}°C" if user_temp else "未提供",
                "temperature": numeric,
                "summary": weather_service.get_suggestion_for_temp(numeric) if numeric is not None else "已使用用户提供的天气信息。",
                "source": "user_input",
                "city": context.city or "",
            }
            return ToolResult("fetch_weather", "completed", "使用用户提供的天气信息。", weather_data)

        try:
            result = weather_service.get_weather(city_name=context.city or None, ip=context.client_ip or None)
            weather_data = {
                "weather": result["condition"],
                "temperature_text": f'{result["temperature"]}°C',
                "temperature": result["temperature"],
                "city": result["city"],
                "humidity": result.get("humidity", ""),
                "wind": result.get("wind", ""),
                "summary": result["suggestion"],
                "source": "auto_query",
            }
            detail = f'已自动获取天气：{result["city"]} {result["condition"]} {result["temperature"]}°C'
            return ToolResult("fetch_weather", "completed", detail, weather_data)
        except Exception as exc:
            logger.warning("weather lookup failed: %s", exc)
            weather_data = {
                "weather": user_weather or "未知",
                "temperature_text": user_temp or "未提供",
                "temperature": None,
                "summary": "未获取到天气信息，建议优先采用可增减层次的稳妥搭配。",
                "source": "fallback",
                "city": context.city or "",
            }
            return ToolResult("fetch_weather", "fallback", "天气查询失败，已切换为兜底建议。", weather_data)

    def _tool_retrieve_knowledge(self, query: str) -> ToolResult:
        docs = self.knowledge_base.search(query)
        return ToolResult("retrieve_knowledge", "completed", f"检索到 {len(docs)} 条穿搭知识。", {"docs": docs})

    def _tool_retrieve_memory(self, context: AgentContext, query: str) -> ToolResult:
        if not context.prefer_wardrobe or not context.user_id:
            return ToolResult("retrieve_memory", "skipped", "未启用用户衣橱记忆。", {"docs": []})
        docs = self.knowledge_base.search_user_memory(context.user_id, query)
        return ToolResult("retrieve_memory", "completed", f"检索到 {len(docs)} 条用户记忆。", {"docs": docs})

    def _tool_generate_plan(
        self,
        *,
        analysis: dict[str, Any],
        knowledge_docs: list[RetrievedDocument],
        memory_docs: list[RetrievedDocument],
        weather_context: dict[str, Any],
        context: AgentContext,
    ) -> ToolResult:
        system_prompt, user_prompt = build_style_plan_prompts(
            analysis=analysis,
            knowledge_docs=knowledge_docs,
            memory_docs=memory_docs,
            weather_context=weather_context,
            occasion=context.occasion,
            notes=context.notes,
        )
        llm_payload = self.llm_client.generate_json(system_prompt, user_prompt)
        normalized = self._normalize_payload(llm_payload)
        if normalized is not None:
            return ToolResult("generate_plan", "completed", "已生成结构化穿搭方案。", normalized)

        fallback = self._build_fallback_recommendation(
            analysis=analysis,
            knowledge_docs=knowledge_docs,
            memory_docs=memory_docs,
            weather_context=weather_context,
            context=context,
        )
        return ToolResult("generate_plan", "fallback", "未拿到有效的 LLM 输出，已切换到规则兜底方案。", fallback)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _langgraph_requested() -> bool:
        try:
            from flask import current_app

            return bool(current_app.config.get("FEATURE_ADVISOR_LANGGRAPH", False))
        except Exception:
            return False

    @staticmethod
    def _emit_progress(
        progress_callback: Callable[[dict[str, Any]], None] | None,
        *,
        step: str,
        label: str,
        detail: str,
        progress: int,
        workflow: dict[str, Any],
    ) -> None:
        if progress_callback is None:
            return
        progress_callback(
            {
                "step": step,
                "label": label,
                "detail": detail,
                "progress": progress,
                "workflow": workflow,
            }
        )

    @staticmethod
    def _build_workflow_descriptor(*, engine: str) -> dict[str, Any]:
        return {
            "engine": engine,
            "graph_available": importlib.util.find_spec("langgraph") is not None,
            "nodes": [
                {"key": "analyze_image", "label": "分析图片"},
                {"key": "fetch_weather", "label": "获取天气"},
                {"key": "retrieve_knowledge", "label": "检索知识库"},
                {"key": "retrieve_memory", "label": "检索衣橱记忆"},
                {"key": "generate_plan", "label": "生成方案"},
            ],
        }

    def _build_result_payload(
        self,
        *,
        analysis: dict[str, Any],
        weather_context: dict[str, Any],
        knowledge_docs: list[RetrievedDocument],
        memory_docs: list[RetrievedDocument],
        recommendation: dict[str, Any],
        trace: list[dict[str, Any]],
        workflow: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "analysis": analysis,
            "weather": weather_context,
            "recommendation": recommendation,
            "knowledge_context": [self._serialize_doc(doc) for doc in knowledge_docs],
            "memory_context": [self._serialize_doc(doc) for doc in memory_docs],
            "agent_trace": trace,
            "workflow": workflow,
        }

    @staticmethod
    def _to_trace(tool: ToolResult) -> dict[str, Any]:
        return {"step": tool.tool_name, "status": tool.status, "detail": tool.detail}

    def _build_retrieval_query(self, analysis: dict[str, Any], context: AgentContext) -> str:
        parts = [
            analysis.get("item_type", ""),
            analysis.get("dominant_color", ""),
            " ".join(analysis.get("style_keywords", [])),
            context.occasion,
            context.weather,
            context.notes,
        ]
        return " ".join([part for part in parts if part]).strip()

    @staticmethod
    def _build_style_keywords(
        style: str,
        caption: str,
        dominant_color: str,
        item_type: str,
        additional_tags: list[str],
    ) -> list[str]:
        keywords: list[str] = []
        if style and style not in {"未知", "日常"}:
            keywords.append(style)
        keywords.extend(additional_tags)

        text = caption.lower()
        if any(token in text for token in ["office", "formal", "tailored"]):
            keywords.append("通勤")
        if any(token in text for token in ["street", "oversized", "cargo"]):
            keywords.append("街头")
        if any(token in text for token in ["soft", "romantic", "feminine"]):
            keywords.append("约会")
        if any(token in text for token in ["casual", "daily", "relaxed"]):
            keywords.append("日常")

        if not keywords:
            if item_type in {"衬衫", "西装上衣"}:
                keywords.extend(["通勤", "极简", "日常"])
            elif item_type in {"牛仔裤", "裤装"}:
                keywords.extend(["日常", "街头"])
            else:
                keywords.extend(["日常", "极简"])

        if dominant_color in {"蓝色", "白色", "灰色"} and "通勤" not in keywords:
            keywords.insert(0, "通勤")

        deduped: list[str] = []
        seen: set[str] = set()
        for keyword in keywords:
            if keyword and keyword not in seen:
                deduped.append(keyword)
                seen.add(keyword)
        return deduped[:3] or ["日常", "极简"]

    def _build_fallback_recommendation(
        self,
        *,
        analysis: dict[str, Any],
        knowledge_docs: list[RetrievedDocument],
        memory_docs: list[RetrievedDocument],
        weather_context: dict[str, Any],
        context: AgentContext,
    ) -> dict[str, Any]:
        item_type = analysis["item_type"]
        dominant_color = analysis["dominant_color"]
        style_tags = list(dict.fromkeys(analysis.get("style_keywords", [])))[:3] or ["日常", "极简"]
        recommended_items = self._fallback_item_suggestions(item_type, dominant_color)
        occasion_label = context.occasion or "日常"

        return {
            "summary": f"建议围绕这件{dominant_color}{item_type}，走“{' / '.join(style_tags)}”方向完成整体搭配。",
            "style_tags": style_tags,
            "narrative": {
                "title": f"{occasion_label}场景下的{style_tags[0]}搭配方案",
                "description": (
                    f"这件{item_type}本身已经具备较明确的颜色和风格指向，"
                    f"适合通过一件稳定的下装、一层平衡气质的外搭，以及一双不抢戏的鞋履完成造型。"
                    f"{weather_context.get('summary', '')}"
                ),
                "why_it_works": [
                    f"{dominant_color}更容易和基础色形成稳定配色。",
                    f"{style_tags[0]}风格可以通过版型和材质继续延展。",
                    "推荐属性已经拆分为可检索条件，便于后续找相似单品。",
                ],
            },
            "recommended_items": recommended_items,
            "retrieval_attributes": {
                "must_have": [f"{dominant_color}协调配色", style_tags[0], recommended_items[0]["keywords"][0]],
                "nice_to_have": ["利落版型", "低饱和配色", weather_context.get("weather", "")],
                "avoid": ["高冲突配色", "过度堆叠装饰"],
            },
            "occasion_fit": f"方案围绕“{occasion_label}”场景做了平衡，兼顾得体与易穿。",
            "weather_fit": weather_context.get("summary", "建议结合当日天气增减层次。"),
            "knowledge_references": [
                {"title": doc.title, "reason": f"用于支撑 {doc.category} 方向的搭配逻辑"}
                for doc in knowledge_docs
            ],
            "memory_references": [
                {"title": doc.title, "reason": "用于贴合用户已有衣橱与偏好"}
                for doc in memory_docs
            ],
            "follow_up_questions": [
                "你更想把这套搭配用于通勤、约会还是休闲出行？",
                "你希望我优先从你的衣橱里复用已有单品吗？",
            ],
        }

    @staticmethod
    def _fallback_item_suggestions(item_type: str, dominant_color: str) -> list[dict[str, Any]]:
        if item_type in {"衬衫", "上装", "T恤", "针织上衣", "西装上衣"}:
            return [
                {
                    "category": "下装",
                    "role": "主搭配",
                    "attributes": {
                        "color": ["深蓝", "黑色"],
                        "material": ["牛仔", "斜纹"],
                        "fit": ["直筒", "高腰"],
                    },
                    "keywords": ["深蓝直筒牛仔裤", "黑色高腰长裤"],
                },
                {
                    "category": "外套",
                    "role": "平衡层",
                    "attributes": {
                        "color": ["米白", "灰色"],
                        "material": ["针织", "西装面料"],
                        "fit": ["短款", "利落"],
                    },
                    "keywords": ["短款针织开衫", "轻薄西装外套"],
                },
                {
                    "category": "鞋履",
                    "role": "收束单品",
                    "attributes": {
                        "color": ["白色", "黑色"],
                        "material": ["皮面", "哑光"],
                        "fit": ["简洁"],
                    },
                    "keywords": ["白色简洁运动鞋", "黑色乐福鞋"],
                },
            ]

        if item_type in {"裤装", "牛仔裤", "半裙", "裙装"}:
            return [
                {
                    "category": "上装",
                    "role": "主搭配",
                    "attributes": {
                        "color": ["白色", dominant_color],
                        "material": ["棉质", "针织"],
                        "fit": ["合身", "利落"],
                    },
                    "keywords": ["白色基础上衣", "修身针织上衣"],
                },
                {
                    "category": "外套",
                    "role": "气质层",
                    "attributes": {
                        "color": ["灰色", "卡其"],
                        "material": ["西装面料"],
                        "fit": ["短款", "挺括"],
                    },
                    "keywords": ["卡其短外套", "灰色轻薄西装"],
                },
                {
                    "category": "鞋履",
                    "role": "点睛单品",
                    "attributes": {
                        "color": ["黑色", "棕色"],
                        "material": ["皮面"],
                        "fit": ["简洁"],
                    },
                    "keywords": ["黑色短靴", "棕色皮鞋"],
                },
            ]

        return [
            {
                "category": "上装",
                "role": "主搭配",
                "attributes": {
                    "color": ["白色", "米色"],
                    "material": ["棉质", "针织"],
                    "fit": ["简洁", "合身"],
                },
                "keywords": ["白色基础上衣", "米色针织上衣"],
            },
            {
                "category": "下装",
                "role": "平衡层",
                "attributes": {
                    "color": ["深蓝", "黑色"],
                    "material": ["牛仔", "斜纹"],
                    "fit": ["直筒", "利落"],
                },
                "keywords": ["深蓝牛仔裤", "黑色直筒裤"],
            },
            {
                "category": "鞋履",
                "role": "收束单品",
                "attributes": {
                    "color": ["白色", "黑色"],
                    "material": ["皮面", "帆布"],
                    "fit": ["低存在感"],
                },
                "keywords": ["白色基础运动鞋", "黑色乐福鞋"],
            },
        ]

    @staticmethod
    def _normalize_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not payload:
            return None
        required_keys = {
            "summary",
            "style_tags",
            "narrative",
            "recommended_items",
            "retrieval_attributes",
            "occasion_fit",
            "weather_fit",
            "knowledge_references",
            "memory_references",
            "follow_up_questions",
        }
        if not required_keys.issubset(payload.keys()):
            return None
        recommended_items = payload.get("recommended_items", [])
        if not isinstance(recommended_items, list) or not recommended_items:
            return None
        payload["style_tags"] = [str(item) for item in payload.get("style_tags", []) if str(item).strip()][:3]
        payload["knowledge_references"] = payload.get("knowledge_references") or []
        payload["memory_references"] = payload.get("memory_references") or []
        payload["follow_up_questions"] = payload.get("follow_up_questions") or []
        return payload

    @staticmethod
    def _serialize_doc(document: RetrievedDocument) -> dict[str, Any]:
        return {
            "document_id": document.document_id,
            "title": document.title,
            "category": document.category,
            "content": document.content,
            "score": document.score,
            "tags": document.tags,
            "metadata": document.metadata,
        }

    def _safe_generate_caption(self, image_path: str) -> str:
        try:
            caption = self.ai_service.generate_caption(image_path)
            if caption and "error" not in caption.lower():
                return caption.strip()
        except Exception:
            logger.exception("caption generation failed")
        return f"a {self._infer_item_type('', image_path)} in {self._infer_color_family_from_path(image_path)} tone"

    @staticmethod
    def _infer_item_type(caption: str, image_path: str) -> str:
        text = f"{caption} {Path(image_path).name}".lower()
        mapping = {
            "衬衫": ["shirt", "blouse"],
            "T恤": ["t-shirt", "tee"],
            "针织上衣": ["knit", "sweater", "cardigan"],
            "西装上衣": ["blazer", "suit jacket"],
            "外套": ["coat", "jacket"],
            "牛仔裤": ["jeans", "denim pants"],
            "裤装": ["pants", "trousers"],
            "半裙": ["skirt"],
            "裙装": ["dress", "gown"],
            "鞋履": ["shoe", "sneaker", "boot", "loafer"],
        }
        for item_type, keywords in mapping.items():
            if any(keyword in text for keyword in keywords):
                return item_type
        return "上装"

    @staticmethod
    def _infer_material_hints(caption: str) -> list[str]:
        text = caption.lower()
        mapping = {
            "牛仔": ["denim"],
            "针织": ["knit", "wool"],
            "棉质": ["cotton"],
            "皮革": ["leather"],
            "丝质": ["silk", "satin"],
            "西装面料": ["tailored", "blazer", "suiting"],
        }
        hints = [label for label, keywords in mapping.items() if any(keyword in text for keyword in keywords)]
        return hints or ["基础面料"]

    @staticmethod
    def _describe_palette(dominant_color: str) -> str:
        mapping = {
            "黑色": "低饱和深色",
            "白色": "干净浅色",
            "蓝色": "清爽冷调",
            "灰色": "中性雾感",
            "棕色": "大地色",
            "绿色": "自然冷调",
            "粉色": "柔和暖调",
            "红色": "高识别暖调",
            "黄色": "明亮轻快",
        }
        return mapping.get(dominant_color, dominant_color)

    @staticmethod
    def _extract_dominant_color(image: Image.Image) -> str:
        array = np.array(image.resize((80, 80))).reshape(-1, 3)
        mean_rgb = array.mean(axis=0)
        red, green, blue = mean_rgb

        if max(mean_rgb) < 55:
            return "黑色"
        if min(mean_rgb) > 215 and np.std(mean_rgb) < 15:
            return "白色"
        if abs(red - green) < 12 and abs(green - blue) < 12:
            return "灰色"
        if blue >= red and blue >= green:
            return "蓝色"
        if red >= blue and red >= green:
            if green > 150:
                return "黄色"
            if blue > 135:
                return "粉色"
            return "红色"
        if green >= red and green >= blue:
            return "棕色" if red > 140 else "绿色"
        return "卡其色"

    @staticmethod
    def _infer_color_family_from_path(image_path: str) -> str:
        filename = Path(image_path).name.lower()
        if "blue" in filename:
            return "blue"
        if "black" in filename:
            return "black"
        if "white" in filename:
            return "white"
        return "neutral"
