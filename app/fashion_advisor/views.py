from __future__ import annotations

import json
import logging
from typing import Any

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context, url_for
from flask_login import current_user

from app.fashion_advisor.prompts import build_chat_prompts
from app.fashion_advisor.services import FashionAdvisorService
from app.fashion_advisor.sse import format_sse

logger = logging.getLogger(__name__)

fashion_advisor_bp = Blueprint("fashion_advisor", __name__, url_prefix="/fashion-advisor")


def _service():
    return FashionAdvisorService()


def _current_user_id():
    if getattr(current_user, "is_authenticated", False):
        return str(current_user.id)
    return None


def _frontend_config() -> dict[str, Any]:
    return {
        "user": {
            "authenticated": bool(getattr(current_user, "is_authenticated", False)),
            "id": _current_user_id(),
            "name": getattr(current_user, "username", "") or "",
        },
        "endpoints": {
            "health": url_for("fashion_advisor.health_check"),
            "advice": url_for("fashion_advisor.get_advice"),
            "chat_stream": url_for("fashion_advisor.chat_stream"),
            "style_plan": url_for("fashion_advisor.generate_style_plan"),
            "style_plan_stream": url_for("fashion_advisor.generate_style_plan_stream"),
            "diagnosis": url_for("fashion_advisor.wardrobe_diagnosis"),
            "reset": url_for("fashion_advisor.reset_conversation"),
        },
        "features": {
            "wardrobe_memory": bool(getattr(current_user, "is_authenticated", False)),
        },
    }


@fashion_advisor_bp.route("/")
def index():
    return render_template(
        "fashion_advisor/fashion_advisor.html",
        frontend_config=_frontend_config(),
    )


@fashion_advisor_bp.route("/api/health", methods=["GET"])
def health_check():
    try:
        return jsonify(_service().health_check())
    except Exception as exc:
        logger.exception("advisor health check failed")
        return jsonify({"status": "error", "error": str(exc)}), 500


@fashion_advisor_bp.route("/api/advice", methods=["POST"])
def get_advice():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = _service().get_fashion_advice(message, user_id=_current_user_id())
        return jsonify(result)
    except Exception as exc:
        logger.exception("get advice failed")
        return jsonify({"error": str(exc)}), 500


@fashion_advisor_bp.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    def generate():
        service = _service()
        user_id = _current_user_id()
        metadata: dict[str, Any] | None = None

        if hasattr(service, "prepare_chat_context"):
            context = service.prepare_chat_context(message, user_id=user_id)
            system_prompt = context["system_prompt"]
            user_prompt = context["user_prompt"]
        else:  # pragma: no cover - compatibility fallback
            memory_docs = service.knowledge_base.search_user_memory(user_id, message) if user_id else []
            knowledge_docs = service.knowledge_base.search(message) if hasattr(service.knowledge_base, "search") else []
            system_prompt, user_prompt = build_chat_prompts(message, memory_docs, knowledge_docs)
            context = {
                "knowledge_context": [],
                "memory_context": [],
                "agent_trace": [],
                "workflow": {"engine": "sequential", "nodes": []},
            }

        yield format_sse(
            {
                "knowledge_context": context.get("knowledge_context", []),
                "memory_context": context.get("memory_context", []),
                "agent_trace": context.get("agent_trace", []),
                "workflow": context.get("workflow", {}),
            },
            event="context",
        )

        token_count = 0
        for token in service.llm_client.generate_stream(system_prompt, user_prompt):
            token_count += 1
            yield format_sse({"token": token}, event="token")

        if token_count == 0 and hasattr(service, "get_fashion_advice"):
            fallback = service.get_fashion_advice(message, user_id=user_id)
            fallback_response = fallback.get("response", "")
            if fallback_response:
                yield format_sse({"token": fallback_response}, event="token")
            metadata = fallback.get("metadata", {})

        yield format_sse(
            {
                "metadata": metadata or {},
                "knowledge_context": context.get("knowledge_context", []),
                "memory_context": context.get("memory_context", []),
                "agent_trace": context.get("agent_trace", []),
                "workflow": context.get("workflow", {}),
            },
            event="meta",
        )
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@fashion_advisor_bp.route("/api/style-plan", methods=["POST"])
def generate_style_plan():
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"success": False, "error": "no image"}), 400

    try:
        result = _service().generate_style_plan(
            image_file=image_file,
            user_id=_current_user_id(),
            occasion=(request.form.get("occasion") or "").strip(),
            weather=(request.form.get("weather") or "").strip(),
            temperature=(request.form.get("temperature") or "").strip(),
            notes=(request.form.get("notes") or "").strip(),
            prefer_wardrobe=(request.form.get("prefer_wardrobe") or "true").lower() in {"1", "true", "on"},
            city=(request.form.get("city") or "").strip(),
        )
        return jsonify(result)
    except Exception as exc:
        logger.exception("style plan failed")
        return jsonify({"success": False, "error": str(exc)}), 500


@fashion_advisor_bp.route("/api/style-plan/stream", methods=["POST"])
def generate_style_plan_stream():
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"success": False, "error": "no image"}), 400

    service = _service()

    def generate():
        for event in service.stream_style_plan_events(
            image_file=image_file,
            user_id=_current_user_id(),
            occasion=(request.form.get("occasion") or "").strip(),
            weather=(request.form.get("weather") or "").strip(),
            temperature=(request.form.get("temperature") or "").strip(),
            notes=(request.form.get("notes") or "").strip(),
            prefer_wardrobe=(request.form.get("prefer_wardrobe") or "true").lower() in {"1", "true", "on"},
            city=(request.form.get("city") or "").strip(),
        ):
            yield format_sse(event["data"], event=event["event"])

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@fashion_advisor_bp.route("/api/diagnosis", methods=["GET"])
def wardrobe_diagnosis():
    try:
        result = _service().get_wardrobe_diagnosis(_current_user_id())
        status = 200 if result.get("success") else 400
        return jsonify(result), status
    except Exception as exc:
        logger.exception("wardrobe diagnosis failed")
        return jsonify({"success": False, "message": str(exc)}), 500


@fashion_advisor_bp.route("/api/reset", methods=["POST"])
def reset_conversation():
    return jsonify({"success": True, "message": "ok"})
