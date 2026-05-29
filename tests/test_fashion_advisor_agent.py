"""Fashion Advisor Agent 单元测试 — 覆盖核心工具方法和兜底逻辑。"""

import pytest
from unittest.mock import MagicMock, patch

from app.fashion_advisor.agent import (
    OutfitAdvisorAgent,
    AgentContext,
    ToolResult,
)
from app.fashion_advisor.llm_client import AdvisorLLMClient
from app.fashion_advisor.knowledge_base import FashionKnowledgeBase
from app.fashion_advisor.prompts import build_style_plan_prompts


class TestAgentContext:
    def test_create_context_with_minimal_fields(self):
        ctx = AgentContext(
            image_path="/tmp/test.jpg",
            user_id=None,
            occasion="日常",
            weather="",
            temperature="",
            notes="",
            prefer_wardrobe=False,
        )
        assert ctx.image_path == "/tmp/test.jpg"
        assert ctx.occasion == "日常"
        assert ctx.prefer_wardrobe is False
        assert ctx.city == ""
        assert ctx.client_ip == ""


class TestOutfitAdvisorAgent:
    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock(spec=AdvisorLLMClient)
        llm.generate_json.return_value = None
        return llm

    @pytest.fixture
    def mock_kb(self):
        kb = MagicMock(spec=FashionKnowledgeBase)
        kb.search.return_value = []
        kb.search_user_memory.return_value = []
        return kb

    @pytest.fixture
    def agent(self, mock_llm, mock_kb):
        return OutfitAdvisorAgent(llm_client=mock_llm, knowledge_base=mock_kb)

    def test_run_sequential_returns_valid_payload(self, agent, mock_llm):
        """顺序执行模式下返回完整的结构化结果。"""
        mock_llm.generate_json.return_value = None  # 强制走 fallback

        ctx = AgentContext(
            image_path="",
            user_id=None,
            occasion="日常",
            weather="晴朗",
            temperature="25",
            notes="",
            prefer_wardrobe=False,
        )

        with patch.object(agent, "_tool_analyze_image") as mock_analyze, \
             patch.object(agent, "_tool_fetch_weather") as mock_weather:
            mock_analyze.return_value = ToolResult(
                "analyze_image", "completed", "done",
                {"item_type": "衬衫", "dominant_color": "白色", "style_keywords": ["日常", "通勤"],
                 "caption": "white shirt", "palette": "干净浅色", "material_hints": ["棉质"],
                 "additional_tags": [], "summary": "test summary"}
            )
            mock_weather.return_value = ToolResult(
                "fetch_weather", "completed", "done",
                {"weather": "晴朗", "temperature": 25, "summary": "天气适宜"}
            )

            result = agent._run_sequential(ctx)

        assert "recommendation" in result
        assert "analysis" in result
        assert "weather" in result
        assert "agent_trace" in result
        assert len(result["agent_trace"]) == 5

    def test_tool_result_serialization(self):
        tr = ToolResult("test_tool", "completed", "一切正常", {"key": "value"})
        trace = OutfitAdvisorAgent._to_trace(tr)
        assert trace["step"] == "test_tool"
        assert trace["status"] == "completed"
        assert trace["detail"] == "一切正常"

    def test_serialize_doc_preserves_keys(self, agent):
        from app.fashion_advisor.knowledge_base import RetrievedDocument
        doc = RetrievedDocument(
            document_id="doc-1",
            title="秋冬叠穿法则",
            category="穿搭知识",
            content="层次感是关键。",
            score=0.92,
            tags=["秋冬", "叠穿"],
            metadata={"source": "manual"},
        )
        serialized = agent._serialize_doc(doc)
        for key in ("document_id", "title", "category", "content", "score", "tags", "metadata"):
            assert key in serialized

    def test_fallback_items_for_top(self, agent):
        """上装类单品应返回下装+外套+鞋履的搭配矩阵。"""
        items = agent._fallback_item_suggestions("衬衫", "白色")
        assert len(items) == 3
        categories = [it["category"] for it in items]
        assert "下装" in categories
        assert "外套" in categories
        assert "鞋履" in categories

    def test_fallback_items_for_bottom(self, agent):
        """下装类单品应返回上装+外套+鞋履的搭配矩阵。"""
        items = agent._fallback_item_suggestions("裤装", "黑色")
        assert len(items) == 3
        categories = [it["category"] for it in items]
        assert "上装" in categories

    def test_style_keywords_dedup(self, agent):
        keywords = agent._build_style_keywords("通勤", "office tailored shirt", "蓝色", "衬衫", [])
        assert len(keywords) <= 3
        assert len(keywords) == len(set(keywords))  # no duplicates

    def test_normalize_payload_rejects_incomplete(self, agent):
        assert agent._normalize_payload(None) is None
        assert agent._normalize_payload({"summary": "hi"}) is None
        assert agent._normalize_payload({"summary": "", "style_tags": [], "narrative": {},
                                          "recommended_items": [], "retrieval_attributes": {},
                                          "occasion_fit": "", "weather_fit": "",
                                          "knowledge_references": [], "memory_references": [],
                                          "follow_up_questions": []}) is None  # empty items


class TestBuildStylePlanPrompts:
    def test_returns_two_strings(self):
        analysis = {"item_type": "连衣裙", "dominant_color": "红色", "style_keywords": ["优雅"]}
        sp, up = build_style_plan_prompts(
            analysis=analysis,
            knowledge_docs=[],
            memory_docs=[],
            weather_context={"weather": "晴", "temperature": 22},
            occasion="约会",
            notes="",
        )
        assert isinstance(sp, str)
        assert isinstance(up, str)
        assert "连衣裙" in up
        assert "红色" in up
