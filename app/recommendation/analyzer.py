"""图像分析模块：基于规则和颜色的服装图片描述与标签解析。"""

import os
import random
import logging

from app.services.image_utils import extract_dominant_color

logger = logging.getLogger(__name__)


def image_to_description(image_path: str, user_style: str | None = None) -> str:
    """基于规则和颜色检测的图片描述生成（不依赖BLIP模型）。"""
    if not os.path.exists(image_path):
        return "时尚服饰单品"

    try:
        # 1. 检测主色调
        dominant_color = extract_dominant_color(image_path)

        # 2. 基于文件名和颜色推断服装类型
        filename = os.path.basename(image_path).lower()

        cloth_type = "服饰"
        type_keywords = [
            (["dress", "skirt", "裙"], "连衣裙"),
            (["shirt", "blouse", "衬衫"], "衬衫"),
            (["pants", "jeans", "trousers", "裤"], "裤子"),
            (["shoe", "sneaker", "boot", "鞋"], "鞋子"),
            (["jacket", "coat", "外套"], "外套"),
            (["hoodie", "sweater", "sweatshirt", "卫衣"], "卫衣"),
            (["t-shirt", "tshirt", "tee", "t恤"], "T恤"),
        ]
        for words, ctype in type_keywords:
            if any(w in filename for w in words):
                cloth_type = ctype
                break

        # 3. 基于颜色和类型生成描述
        color_descriptions = {
            "黑色": "经典黑色", "白色": "纯净白色", "红色": "热情红色",
            "蓝色": "沉稳蓝色", "绿色": "清新绿色", "黄色": "明亮黄色",
            "粉色": "温柔粉色", "紫色": "神秘紫色", "灰色": "高级灰色",
            "棕色": "复古棕色", "橙色": "活力橙色", "其他": "时尚",
        }

        color_desc = color_descriptions.get(dominant_color, "时尚")

        # 4. 风格推断
        if user_style:
            style = user_style
        else:
            style_keywords = {
                "黑色": "简约风", "白色": "清新风", "红色": "活力风",
                "蓝色": "休闲风", "绿色": "自然风", "黄色": "阳光风",
                "粉色": "甜美风", "紫色": "优雅风", "灰色": "商务风",
                "棕色": "复古风", "橙色": "运动风",
            }
            style = style_keywords.get(dominant_color, "潮流风")

        # 5. 组合描述
        descriptions = [
            f"{color_desc}{cloth_type}，{style}设计，适合日常穿搭",
            f"{style}{cloth_type}，主色调为{dominant_color}，时尚百搭",
            f"{color_desc}{cloth_type}，展现{style}魅力，适配多种场合",
            f"{cloth_type}单品，{dominant_color}系{style}，穿搭优选",
        ]

        return random.choice(descriptions)

    except Exception as e:
        logger.error("规则描述生成失败: %s", e)
        return "时尚服饰单品，适合多种场合穿搭"


def parse_cloth_type(description: str) -> str:
    """从纯中文描述中解析衣物类型（全中文匹配）。"""
    type_mapping: dict[str, list[str]] = {
        "衬衫": ["衬衫", "寸衫"],
        "T恤": ["t恤", "短袖", "体恤"],
        "毛衣": ["毛衣", "针织衫", "毛衫"],
        "卫衣": ["卫衣", "连帽衫"],
        "外套": ["外套", "夹克", "西装", "大衣", "风衣"],
        "裤子": ["裤子", "长裤", "西裤"],
        "牛仔裤": ["牛仔裤", "牛仔裤"],
        "短裤": ["短裤", "五分裤", "七分裤"],
        "裙子": ["裙子", "半身裙"],
        "连衣裙": ["连衣裙", "长裙", "短裙"],
        "鞋子": ["鞋子", "运动鞋", "靴子", "皮鞋", "跑鞋"],
        "帽子": ["帽子", "棒球帽", "鸭舌帽"],
        "围巾": ["围巾", "围脖"],
    }
    for cloth_type, keywords in type_mapping.items():
        if any(kw in description for kw in keywords):
            return cloth_type
    return "服饰"


def parse_style_tag(description: str) -> str:
    """从纯中文描述中解析风格标签（全中文匹配）。"""
    style_mapping: dict[str, list[str]] = {
        "街头风": ["街头", "潮流", "个性", "嘻哈"],
        "优雅风": ["优雅", "气质", "知性", "端庄"],
        "休闲风": ["休闲", "日常", "舒适", "百搭"],
        "运动风": ["运动", "活力", "轻便", "健身"],
        "复古风": ["复古", "怀旧", "经典", "老式"],
        "极简风": ["极简", "简约", "大气", "简洁"],
        "甜美风": ["甜美", "可爱", "清新", "少女"],
        "正式风": ["正式", "商务", "得体", "端庄"],
    }
    for style, keywords in style_mapping.items():
        if any(kw in description for kw in keywords):
            return style
    return "通用风"
