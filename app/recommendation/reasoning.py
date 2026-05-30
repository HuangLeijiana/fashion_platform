"""推荐理由生成模块：基于用户画像、天气和单品信息生成自然语言推荐理由。"""

import json
from typing import Any


def build_recommend_reason(
    rec: dict[str, Any],
    profile: Any | None,
    city: str,
    temp: float,
    condition: str,
) -> str:
    """使用用户画像 + 天气 + 单品信息生成推荐理由（规则驱动）。"""
    parts: list[str] = []
    prefix = "【我的衣柜】" if rec.get("is_wardrobe") else "【精选推荐】"
    cloth_type = rec.get("cloth_type") or "单品"
    similarity = rec.get("similarity", 0.0)
    style_tag = str(rec.get("style_tag") or "")
    desc = str(rec.get("description") or "")
    weather_suggestion = rec.get("weather_suggestion") or ""

    # 1. 基于相似度的总体评价
    if similarity >= 0.85:
        match_text = "与您上传的图片风格高度契合"
    elif similarity >= 0.65:
        match_text = "整体风格与您上传的图片非常相近"
    elif similarity >= 0.45:
        match_text = "在色彩和风格上与您上传的图片有不错的呼应"
    else:
        match_text = "在风格上与您上传的图片形成互补"

    parts.append(f"{prefix}{match_text}，为您优先挑选了一件{cloth_type}。")

    # 2. 利用用户画像做"个人化"解释
    if profile:
        _add_profile_reason(profile, parts, rec, style_tag, desc)

    # 3. 气温与天气场景的说明
    if city and weather_suggestion:
        parts.append(
            f"考虑到当前{city}{condition}、气温约 {int(temp)}℃，{weather_suggestion}"
        )
    elif weather_suggestion:
        parts.append(weather_suggestion)

    # 4. 轻微点题
    if "中式" in style_tag or "旗袍" in desc:
        parts.append(
            "整体偏中式风格，既有仪式感，又不会过于张扬，"
            "适合作为日常与稍正式场合之间的过渡搭配。"
        )

    return " ".join(p.strip() for p in parts if p and p.strip())


def _add_profile_reason(
    profile: Any,
    parts: list[str],
    rec: dict[str, Any],
    style_tag: str,
    desc: str,
) -> None:
    """填充基于用户画像的个性化理由（内部辅助函数）。"""
    persona_bits = []
    if profile.height:
        persona_bits.append(f"身高约 {int(profile.height)}cm")
    if profile.weight:
        persona_bits.append(f"体重约 {int(profile.weight)}kg")
    if profile.body_shape:
        persona_bits.append(f"{profile.body_shape}身材")
    if profile.skin_tone:
        persona_bits.append(f"{profile.skin_tone}肤色")

    persona_text = "、".join(persona_bits)

    # 体型相关建议
    body_shape_reasons = {
        "梨形": "下半身易显重，因此选择版型相对利落的单品，可以在视觉上拉长比例、弱化臀胯宽度。",
        "梨型": "下半身易显重，因此选择版型相对利落的单品，可以在视觉上拉长比例、弱化臀胯宽度。",
        "苹果形": "上半身容易显得饱满，这类单品在肩线和整体线条上相对干净，有助于弱化上半身体积感。",
        "苹果型": "上半身容易显得饱满，这类单品在肩线和整体线条上相对干净，有助于弱化上半身体积感。",
        "沙漏形": "沙漏型身材腰线优势明显，这类单品可以把腰线自然强调出来，整体更有曲线感。",
        "沙漏型": "沙漏型身材腰线优势明显，这类单品可以把腰线自然强调出来，整体更有曲线感。",
        "矩形": '矩形身材直线感较强，这类单品在轮廓和细节上增加了一点层次感，能让整体不那么“直上直下”。',
        "H型": '矩形身材直线感较强，这类单品在轮廓和细节上增加了一点层次感，能让整体不那么“直上直下”。',
    }
    body_reason = body_shape_reasons.get(
        profile.body_shape, ""
    ) if profile.body_shape else ""

    # 肤色与颜色协同
    color_reason = ""
    color = str(rec.get("color") or "")
    if profile.skin_tone and color:
        if profile.skin_tone in ("白皙", "自然") and any(
            c in color for c in ["黑", "藏蓝", "深色"]
        ):
            color_reason = "深色系在您偏亮的肤色下对比感会更强，整体更显气质。"
        elif profile.skin_tone in ("小麦色", "深色") and any(
            c in color for c in ["米色", "驼色", "卡其"]
        ):
            color_reason = "偏大地色的色系和小麦色肤色的明度比较接近，看起来会更温和、质感更好。"

    if persona_text or body_reason or color_reason:
        detail_sentences = []
        if persona_text:
            detail_sentences.append(f"结合您当前的{persona_text}，")
        if body_reason:
            detail_sentences.append(body_reason)
        if color_reason:
            detail_sentences.append(color_reason)
        parts.append("".join(detail_sentences))

    # 风格偏好与推荐风格的匹配
    preferred = _parse_style_preferences(profile)
    if preferred:
        hit = [s for s in preferred if s and s in style_tag]
        if hit:
            parts.append(
                f"这件单品在风格上贴近您标记的「{'、'.join(hit)}」偏好，"
                "穿上会更符合您一贯的审美。"
            )
        else:
            parts.append(
                "在风格上我们刻意做了些差异，"
                "让它在保持整体协调的前提下，给您的日常穿搭带来一点新鲜感。"
            )


def _parse_style_preferences(profile: Any) -> list[str]:
    """从用户画像中解析风格偏好列表。"""
    try:
        if profile.style_pref:
            if isinstance(profile.style_pref, str):
                if profile.style_pref.strip().startswith("["):
                    return json.loads(profile.style_pref)
                return [profile.style_pref]
            if isinstance(profile.style_pref, list):
                return profile.style_pref
    except Exception:
        pass
    return []
