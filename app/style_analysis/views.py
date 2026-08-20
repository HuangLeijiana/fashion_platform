import json
from collections import Counter

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.extensions import allowed_file
from app.models import ClothingItem

style_analysis_bp = Blueprint("style_analysis", __name__, template_folder="../../templates")


@style_analysis_bp.route("/")
@login_required
def analysis():
    return render_template("style_analysis/analysis.html")


@style_analysis_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"error": "请先上传一张图片"}), 400

    if not allowed_file(image.filename):
        return jsonify({"error": "仅支持 png、jpg、jpeg、gif、webp 格式图片"}), 400

    return jsonify({
        "error": "风格分析模型尚未配置，请添加 app/style_analysis/style_model.pth 后重试"
    })


@style_analysis_bp.route("/generate_profile", methods=["POST"])
@login_required
def generate_profile():
    items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    style_counts = Counter()

    for item in items:
        for tag in _parse_style_tags(item.style_tags):
            style_counts[tag] += 1

    total = sum(style_counts.values())
    if total == 0:
        return jsonify({
            "success": True,
            "data": {
                "style_distribution": {},
                "report": "当前衣柜暂无可用风格标签，添加带有风格标签的单品后可生成个人风格画像。",
            },
        })

    distribution = {
        style: round(count / total * 100, 1)
        for style, count in style_counts.most_common()
    }
    dominant_style = style_counts.most_common(1)[0][0]

    return jsonify({
        "success": True,
        "data": {
            "style_distribution": distribution,
            "report": (
                f"系统分析了你衣柜中的 {len(items)} 件单品，"
                f"当前主风格倾向为「{dominant_style}」。"
                "该画像可用于后续推荐结果的个性化调整。"
            ),
        },
    })


def _parse_style_tags(raw_tags):
    if not raw_tags:
        return []

    if isinstance(raw_tags, list):
        return [tag.strip() for tag in raw_tags if isinstance(tag, str) and tag.strip()]

    try:
        parsed = json.loads(raw_tags)
    except (TypeError, json.JSONDecodeError):
        parsed = raw_tags

    if isinstance(parsed, list):
        return [tag.strip() for tag in parsed if isinstance(tag, str) and tag.strip()]

    if isinstance(parsed, str):
        return [tag.strip() for tag in parsed.split(",") if tag.strip()]

    return []
