from __future__ import annotations

from typing import Iterable

from app.fashion_advisor.knowledge_base import RetrievedDocument


STYLE_PLAN_SCHEMA_DESCRIPTION = """
请严格返回 JSON，不要输出 Markdown，不要附加解释。JSON 结构必须包含：
{
  "summary": "一句话总结",
  "style_tags": ["通勤", "极简", "约会"],
  "narrative": {
    "title": "本次搭配标题",
    "description": "一段完整的个性化穿搭文案",
    "why_it_works": ["理由1", "理由2", "理由3"]
  },
  "recommended_items": [
    {
      "category": "下装/外套/鞋履/包袋",
      "role": "主搭配/平衡层/点睛单品",
      "attributes": {
        "color": ["深蓝", "白色"],
        "material": ["牛仔", "针织"],
        "fit": ["直筒", "短款", "利落"]
      },
      "keywords": ["深蓝直筒牛仔裤", "短款针织开衫"]
    }
  ],
  "retrieval_attributes": {
    "must_have": ["必须具备的检索条件"],
    "nice_to_have": ["可选检索条件"],
    "avoid": ["不建议出现的元素"]
  },
  "occasion_fit": "为什么适合这个场景",
  "weather_fit": "为什么适合当前天气",
  "knowledge_references": [
    {
      "title": "引用到的知识条目标题",
      "reason": "引用原因"
    }
  ],
  "memory_references": [
    {
      "title": "用户衣橱或历史偏好条目",
      "reason": "如何沿用用户已有偏好"
    }
  ],
  "follow_up_questions": ["追问1", "追问2"]
}
"""


def build_style_plan_prompts(
    *,
    analysis: dict,
    knowledge_docs: Iterable[RetrievedDocument],
    memory_docs: Iterable[RetrievedDocument],
    weather_context: dict,
    occasion: str,
    notes: str,
) -> tuple[str, str]:
    system_prompt = (
        "你是一名资深个人形象顾问和穿搭策划师。"
        "你会结合图片分析、场景、天气、知识库和用户历史偏好，"
        "生成既有审美表达又方便系统检索的结构化穿搭建议。"
        "所有输出必须是自然中文，并且严格遵守给定 JSON 结构。"
    )

    knowledge_block = _format_docs("知识库检索结果", knowledge_docs)
    memory_block = _format_docs("用户历史偏好 / 衣橱记忆", memory_docs)

    user_prompt = f"""
请基于以下输入，输出一份高质量、结构化、可直接给前端使用的穿搭方案。

【图片分析结果】
主单品类型：{analysis.get("item_type", "")}
主色调：{analysis.get("dominant_color", "")}
风格关键词：{", ".join(analysis.get("style_keywords", []))}
材质线索：{", ".join(analysis.get("material_hints", []))}
多模态描述：{analysis.get("caption", "")}
分析摘要：{analysis.get("summary", "")}

【场景与天气】
场合：{occasion or "未指定，默认按日常/通勤处理"}
天气：{weather_context.get("weather", "未知")}
温度：{weather_context.get("temperature_text", "未知")}
天气建议：{weather_context.get("summary", "默认按室内常温场景估计")}

【补充需求】
{notes or "无额外补充"}

【知识增强】
{knowledge_block}

【用户记忆增强】
{memory_block}

【输出要求】
1. 文案必须像专业顾问说话，不能机械列点。
2. 推荐理由要明确说明为什么这样搭配。
3. recommended_items 至少给出 3 个搭配方向。
4. retrieval_attributes 必须适合后续商品检索。
5. 如果引用了知识库或用户记忆，请写入对应 references。
6. 绝对不要输出问号占位符、乱码、Markdown 代码块。

{STYLE_PLAN_SCHEMA_DESCRIPTION}
""".strip()

    return system_prompt, user_prompt


def build_chat_prompts(
    message: str,
    memory_docs: Iterable[RetrievedDocument],
    knowledge_docs: Iterable[RetrievedDocument] = (),
) -> tuple[str, str]:
    system_prompt = (
        "你是一名中文时尚顾问。"
        "请用自然、具体、简洁的中文回答用户问题。"
        "如果有用户历史偏好，请尽量贴合，但不要编造不存在的信息。"
    )
    knowledge_block = _format_docs("穿搭知识参考", knowledge_docs)
    memory_block = _format_docs("用户偏好参考", memory_docs)
    user_prompt = f"""
用户问题：{message}

{knowledge_block}

{memory_block}

请直接输出中文回答，不要输出 JSON，不要出现占位符或乱码。
""".strip()
    return system_prompt, user_prompt


def _format_docs(title: str, documents: Iterable[RetrievedDocument]) -> str:
    items = list(documents)
    if not items:
        return f"{title}：无"

    lines = [f"{title}："]
    for index, document in enumerate(items, start=1):
        lines.append(
            f"{index}. 标题：{document.title}；分类：{document.category}；内容：{document.content}"
        )
    return "\n".join(lines)
