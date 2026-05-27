import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.services.llm_observability import LLMObservability


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_llm_observability_records_metrics(tmp_path):
    log_path = tmp_path / "llm_metrics.log"
    observability = LLMObservability(str(log_path))

    payload = observability.record(
        provider="openai-compatible",
        model="test-model",
        started_at=0.0,
        prompt_text="你好，帮我推荐一套通勤穿搭",
        response_text="可以选择白衬衫搭配深色直筒裤。",
        success=True,
    )

    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "test-model"
    assert payload["estimated_total_tokens"] >= payload["estimated_input_tokens"]
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["success"] is True


def test_fashion_advisor_stream_endpoint(client, monkeypatch):
    import app.fashion_advisor.views as advisor_views

    class FakeLLMClient:
        def generate_stream(self, system_prompt, user_prompt):
            yield "你好"
            yield "，建议先从基础色开始。"

    class FakeService:
        def __init__(self):
            self.llm_client = FakeLLMClient()

        def prepare_chat_context(self, message, user_id=None):
            return {
                "system_prompt": "system",
                "user_prompt": message,
                "knowledge_context": [{"document_id": "k1", "title": "通勤配色", "score": 0.9}],
                "memory_context": [],
                "agent_trace": [{"step": "retrieve_knowledge", "status": "completed", "detail": "检索到 1 条知识。"}],
                "workflow": {"engine": "sequential", "nodes": [{"key": "retrieve_knowledge", "label": "检索知识库"}]},
            }

    monkeypatch.setattr(advisor_views, "_service", lambda: FakeService())

    response = client.post("/fashion-advisor/api/chat/stream", json={"message": "你好"})
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "event: context" in body
    assert '"token": "你好"' in body
    assert '"token": "，建议先从基础色开始。"' in body
    assert "event: meta" in body
    assert "[DONE]" in body


def test_fashion_advice_returns_metrics(client, monkeypatch):
    import app.fashion_advisor.services as advisor_services

    class FakeResult:
        provider = "ollama"
        model = "qwen2.5:3b"
        content = "建议你用白衬衫搭配深色下装。"
        metadata = {"latency_ms": 12, "estimated_total_tokens": 42}

    class FakeKnowledgeBase:
        def __init__(self, top_k=3):
            self.top_k = top_k

        def search(self, query):
            return []

        def search_user_memory(self, user_id, message):
            return []

    monkeypatch.setattr(advisor_services, "FashionKnowledgeBase", FakeKnowledgeBase)
    monkeypatch.setattr(
        advisor_services.AdvisorLLMClient,
        "generate_text",
        lambda self, system_prompt, user_prompt, temperature=0.5: FakeResult(),
    )

    service = advisor_services.FashionAdvisorService()
    result = service.get_fashion_advice("帮我推荐通勤穿搭")

    assert result["metadata"]["provider"] == "ollama"
    assert result["metadata"]["metrics"]["latency_ms"] == 12
    assert result["workflow"]["engine"] == "sequential"


def test_style_plan_stream_endpoint(client, monkeypatch):
    import io
    import app.fashion_advisor.views as advisor_views

    class FakeService:
        def stream_style_plan_events(self, **kwargs):
            yield {
                "event": "progress",
                "data": {
                    "step": "analyze_image",
                    "label": "分析图片",
                    "detail": "完成主单品识别。",
                    "progress": 20,
                    "workflow": {"engine": "sequential", "nodes": []},
                },
            }
            yield {
                "event": "result",
                "data": {
                    "success": True,
                    "analysis": {"summary": "识别为白色衬衫"},
                    "recommendation": {"summary": "建议搭配深色长裤"},
                    "agent_trace": [],
                    "workflow": {"engine": "sequential", "nodes": []},
                },
            }
            yield {"event": "done", "data": {"ok": True}}

    monkeypatch.setattr(advisor_views, "_service", lambda: FakeService())

    response = client.post(
        "/fashion-advisor/api/style-plan/stream",
        data={"image": (io.BytesIO(b"fake-image"), "shirt.png")},
        content_type="multipart/form-data",
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "event: progress" in body
    assert "event: result" in body
    assert "分析图片" in body
