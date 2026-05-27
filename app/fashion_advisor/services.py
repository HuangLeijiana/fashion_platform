from __future__ import annotations

import os
import tempfile
from queue import Queue
from threading import Thread
from typing import Any, Callable, Generator

from flask import current_app, request

from app.fashion_advisor.agent import AgentContext, OutfitAdvisorAgent
from app.fashion_advisor.knowledge_base import FashionKnowledgeBase, RetrievedDocument
from app.fashion_advisor.llm_client import AdvisorLLMClient
from app.fashion_advisor.prompts import build_chat_prompts
from app.models import ClothingItem


class FashionAdvisorService:
    """AI fashion advisor service."""

    def __init__(self) -> None:
        self.llm_client = AdvisorLLMClient()
        top_k = current_app.config.get("ADVISOR_VECTOR_TOP_K", 3)
        self.knowledge_base = FashionKnowledgeBase(top_k=top_k)
        self.agent = OutfitAdvisorAgent(self.llm_client, self.knowledge_base)

    def health_check(self) -> dict[str, Any]:
        llm_status = self.llm_client.health()
        advisor_bundle = os.path.join(current_app.static_folder or "", "advisor-app", "fashion-advisor-app.js")
        return {
            "status": "success",
            "service": "fashion_advisor",
            "llm": llm_status,
            "rag_enabled": current_app.config.get("FEATURE_ADVISOR_RAG", True),
            "agent_enabled": current_app.config.get("FEATURE_ADVISOR_AGENT", True),
            "streaming_enabled": True,
            "langgraph_enabled": current_app.config.get("FEATURE_ADVISOR_LANGGRAPH", False),
            "langgraph_available": self._langgraph_available(),
            "frontend_ready": os.path.exists(advisor_bundle),
            "observability_log": "logs/llm_metrics.log",
        }

    def prepare_chat_context(
        self,
        message: str,
        *,
        user_id: str | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        workflow = {
            "engine": "sequential",
            "graph_available": self._langgraph_available(),
            "nodes": [
                {"key": "retrieve_knowledge", "label": "检索知识库"},
                {"key": "retrieve_memory", "label": "检索衣橱记忆"},
                {"key": "generate_reply", "label": "生成回复"},
            ],
        }

        knowledge_docs = self.knowledge_base.search(message)
        trace = [
            {
                "step": "retrieve_knowledge",
                "status": "completed",
                "detail": f"检索到 {len(knowledge_docs)} 条穿搭知识。",
            }
        ]
        self._emit_progress(
            progress_callback,
            step="retrieve_knowledge",
            label="检索知识库",
            detail=trace[-1]["detail"],
            progress=34,
            workflow=workflow,
        )

        memory_docs = self.knowledge_base.search_user_memory(user_id, message) if user_id else []
        memory_status = "completed" if user_id else "skipped"
        memory_detail = (
            f"检索到 {len(memory_docs)} 条衣橱记忆。"
            if user_id
            else "当前未登录，未启用衣橱记忆。"
        )
        trace.append({"step": "retrieve_memory", "status": memory_status, "detail": memory_detail})
        self._emit_progress(
            progress_callback,
            step="retrieve_memory",
            label="检索衣橱记忆",
            detail=memory_detail,
            progress=68,
            workflow=workflow,
        )

        system_prompt, user_prompt = build_chat_prompts(message, memory_docs, knowledge_docs)
        trace.append(
            {
                "step": "generate_reply",
                "status": "ready",
                "detail": "上下文已准备完成，正在等待大模型生成回复。",
            }
        )
        self._emit_progress(
            progress_callback,
            step="generate_reply",
            label="生成回复",
            detail=trace[-1]["detail"],
            progress=92,
            workflow=workflow,
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "knowledge_docs": knowledge_docs,
            "memory_docs": memory_docs,
            "knowledge_context": self._serialize_docs(knowledge_docs),
            "memory_context": self._serialize_docs(memory_docs),
            "agent_trace": trace,
            "workflow": workflow,
        }

    def get_fashion_advice(self, message: str, user_id: str | None = None) -> dict[str, Any]:
        context = self.prepare_chat_context(message, user_id=user_id)
        result = self.llm_client.generate_text(
            context["system_prompt"],
            context["user_prompt"],
            temperature=0.5,
        )
        if result is not None and result.content.strip():
            response_text = result.content.strip()
            provider = result.provider
            model = result.model
            metrics = result.metadata or {}
        else:
            response_text = self._build_fallback_chat_reply(message, context["memory_docs"], context["knowledge_docs"])
            provider = "fallback"
            model = "rule-based"
            metrics = {}

        return {
            "response": response_text,
            "metadata": {
                "provider": provider,
                "model": model,
                "metrics": metrics,
            },
            "knowledge_context": context["knowledge_context"],
            "memory_context": context["memory_context"],
            "agent_trace": context["agent_trace"],
            "workflow": context["workflow"],
        }

    def generate_style_plan(
        self,
        *,
        image_file,
        user_id: str | None = None,
        occasion: str = "",
        weather: str = "",
        temperature: str = "",
        notes: str = "",
        prefer_wardrobe: bool = True,
        city: str = "",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        suffix = os.path.splitext(image_file.filename or "")[1] or ".jpg"
        temp_path = self._save_upload_to_temp(image_file, suffix=suffix)
        try:
            return self._run_style_plan_from_path(
                image_path=temp_path,
                user_id=user_id,
                occasion=occasion,
                weather=weather,
                temperature=temperature,
                notes=notes,
                prefer_wardrobe=prefer_wardrobe,
                city=city,
                client_ip=request.remote_addr if request else "",
                progress_callback=progress_callback,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def stream_style_plan_events(
        self,
        *,
        image_file,
        user_id: str | None = None,
        occasion: str = "",
        weather: str = "",
        temperature: str = "",
        notes: str = "",
        prefer_wardrobe: bool = True,
        city: str = "",
    ) -> Generator[dict[str, Any], None, None]:
        suffix = os.path.splitext(image_file.filename or "")[1] or ".jpg"
        temp_path = self._save_upload_to_temp(image_file, suffix=suffix)
        app = current_app._get_current_object()
        client_ip = request.remote_addr if request else ""
        event_queue: Queue[tuple[str, dict[str, Any]]] = Queue()

        def progress_callback(payload: dict[str, Any]) -> None:
            event_queue.put(("progress", payload))

        def worker() -> None:
            try:
                with app.app_context():
                    result = self._run_style_plan_from_path(
                        image_path=temp_path,
                        user_id=user_id,
                        occasion=occasion,
                        weather=weather,
                        temperature=temperature,
                        notes=notes,
                        prefer_wardrobe=prefer_wardrobe,
                        city=city,
                        client_ip=client_ip,
                        progress_callback=progress_callback,
                    )
                    event_queue.put(("result", result))
            except Exception as exc:
                event_queue.put(("error", {"message": str(exc)}))
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                event_queue.put(("done", {"ok": True}))

        Thread(target=worker, daemon=True).start()

        while True:
            event, payload = event_queue.get()
            yield {"event": event, "data": payload}
            if event in {"error", "done"}:
                break

    def _run_style_plan_from_path(
        self,
        *,
        image_path: str,
        user_id: str | None,
        occasion: str,
        weather: str,
        temperature: str,
        notes: str,
        prefer_wardrobe: bool,
        city: str,
        client_ip: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        context = AgentContext(
            image_path=image_path,
            user_id=user_id,
            occasion=occasion.strip(),
            weather=weather.strip(),
            temperature=temperature.strip(),
            notes=notes.strip(),
            prefer_wardrobe=prefer_wardrobe,
            city=city.strip(),
            client_ip=client_ip,
        )
        result = self.agent.run(context, progress_callback=progress_callback)
        return {"success": True, **result}

    def get_wardrobe_diagnosis(self, user_id: str | None) -> dict[str, Any]:
        if not user_id:
            return {"success": False, "message": "请先登录后再使用衣橱诊断。"}

        items = ClothingItem.query.filter_by(user_id=user_id).all()
        if not items:
            return {"success": False, "message": "衣橱为空，请先添加衣物。"}

        color_distribution: dict[str, int] = {}
        category_distribution: dict[str, int] = {}
        style_distribution: dict[str, int] = {}

        for item in items:
            color = item.color or "未标注"
            category = item.category or "未分类"
            style = item.occasion or "日常"
            color_distribution[color] = color_distribution.get(color, 0) + 1
            category_distribution[category] = category_distribution.get(category, 0) + 1
            style_distribution[style] = style_distribution.get(style, 0) + 1

        diagnosis: list[str] = []
        if category_distribution.get("裤装", 0) + category_distribution.get("牛仔裤", 0) + category_distribution.get("半裙", 0) < 2:
            diagnosis.append("下装偏少，建议补一条深色长裤和一条更轻松的日常下装。")
        if color_distribution.get("白色", 0) < 1:
            diagnosis.append("缺少白色基础款，建议补一件白色内搭或衬衫，提升搭配灵活性。")
        if category_distribution.get("外套", 0) < 1 and category_distribution.get("西装上衣", 0) < 1:
            diagnosis.append("外搭层偏少，建议补一件轻薄外套或针织开衫，增强天气适配能力。")
        if len(style_distribution) <= 2:
            diagnosis.append("当前风格集中度较高，可以加入一些不同场景的单品，让衣橱更有变化。")
        if not diagnosis:
            diagnosis.append("衣橱结构比较均衡，基础款与风格款之间的搭配空间不错。")

        tops = [item for item in items if (item.category or "") in {"上装", "衬衫", "T恤", "针织上衣", "外套", "西装上衣"}]
        bottoms = [item for item in items if (item.category or "") in {"裤装", "牛仔裤", "半裙", "裙装"}]

        outfit_recommendations: list[dict[str, Any]] = []
        for top in tops[:3]:
            for bottom in bottoms[:3]:
                outfit_recommendations.append(
                    {
                        "top_name": top.name,
                        "bottom_name": bottom.name,
                        "pair_index": len(outfit_recommendations) + 1,
                    }
                )

        purchase_advice: list[dict[str, str]] = []
        if color_distribution.get("黑色", 0) < 1:
            purchase_advice.append({"type": "基础款下装", "color": "黑色", "season": "四季", "reason": "黑色下装最容易承接多种上装。"})
        if category_distribution.get("鞋履", 0) < 1:
            purchase_advice.append({"type": "鞋履", "color": "白色或黑色", "season": "四季", "reason": "一双简洁鞋履能显著提升搭配完成度。"})

        return {
            "success": True,
            "color_distribution": color_distribution,
            "category_distribution": category_distribution,
            "style_distribution": style_distribution,
            "diagnosis": diagnosis,
            "outfit_recommendations": outfit_recommendations[:3],
            "purchase_advice": purchase_advice,
        }

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
    def _save_upload_to_temp(image_file, *, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            image_file.save(handle.name)
            return handle.name

    @staticmethod
    def _serialize_docs(documents: list[RetrievedDocument]) -> list[dict[str, Any]]:
        return [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "score": doc.score,
                "tags": doc.tags,
                "metadata": doc.metadata,
            }
            for doc in documents
        ]

    @staticmethod
    def _langgraph_available() -> bool:
        import importlib.util

        return importlib.util.find_spec("langgraph") is not None

    @staticmethod
    def _build_fallback_chat_reply(
        message: str,
        memory_docs: list[RetrievedDocument],
        knowledge_docs: list[RetrievedDocument],
    ) -> str:
        sections = ["我先按实用角度给你一个稳妥建议："]
        if "通勤" in message or "上班" in message or "会议" in message:
            sections.append("优先选择利落上装搭配深色直筒下装，再用简洁鞋履收尾。")
        elif "约会" in message:
            sections.append("可以保留一点柔和对比，比如挺括上装配柔软下装，整体会更自然。")
        elif "周末" in message or "休闲" in message:
            sections.append("版型可以更放松，但颜色最好控制在三种以内，显得更干净。")
        else:
            sections.append("可以优先围绕“颜色协调 + 版型平衡 + 场景适配”这三个维度来搭配。")

        if memory_docs:
            sections.append("我会尽量贴合你现有衣橱和偏好，避免给出太跳脱的建议。")
        if knowledge_docs:
            sections.append(f"这次也参考了 {len(knowledge_docs)} 条穿搭知识，让建议更具体。")
        sections.append("如果你愿意，也可以上传一张单品图片，我再帮你做更细的搭配方案。")
        return "".join(sections)
