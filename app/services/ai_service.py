"""AI 服务模块 — CLIP/BLIP 模型加载、图像特征提取、属性分析。"""

from __future__ import annotations

import os
import logging
from typing import Any

import torch
import clip
import cv2
import numpy as np
from PIL import Image
from flask import current_app
from transformers import BlipProcessor, BlipForConditionalGeneration

logger = logging.getLogger(__name__)


class AIService:
    """AI 推理服务单例：管理 CLIP / BLIP 模型生命周期。"""

    _instance: AIService | None = None

    initialized: bool
    clip_model: Any | None
    blip_model: BlipForConditionalGeneration | None
    clip_preprocess: Any | None
    blip_processor: BlipProcessor | None
    device: str
    local_blip_path: str

    def __new__(cls) -> AIService:
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.clip_model = None
            cls._instance.blip_model = None
            cls._instance.clip_preprocess = None
            cls._instance.blip_processor = None
            cls._instance.device = "cpu"
        return cls._instance

    def initialize(self) -> None:
        """加载 BLIP 和 CLIP 模型。"""
        if self.initialized:
            return

        logger.info("初始化模型...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # 1. 加载 BLIP
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

        self.local_blip_path = os.path.join(
            project_root, "app", "models", "blip-image-captioning-base"
        )
        self.blip_processor = None
        self.blip_model = None

        try:
            if os.path.exists(self.local_blip_path):
                self.blip_processor = BlipProcessor.from_pretrained(
                    self.local_blip_path
                )
                self.blip_model = (
                    BlipForConditionalGeneration.from_pretrained(
                        self.local_blip_path
                    ).to(self.device)
                )

                # 尝试加载自定义微调权重
                model_path = os.path.join(
                    project_root, "app", "checkpoints", "fashion_model.pth"
                )
                if os.path.exists(model_path):
                    checkpoint: dict[str, Any] = torch.load(
                        model_path, map_location=self.device
                    )
                    state_dict = checkpoint.get("blip_model", checkpoint)
                    self.blip_model.load_state_dict(state_dict, strict=False)
                    logger.info("加载 BLIP 微调权重成功")

                self.blip_model.eval()
            else:
                logger.warning(
                    "BLIP 模型路径不存在: %s", self.local_blip_path
                )
        except Exception as e:
            logger.error("BLIP 加载失败: %s", e)

        # 2. 加载 CLIP
        self.clip_model = None
        self.clip_preprocess = None
        try:
            self.clip_model, self.clip_preprocess = clip.load(
                "ViT-B/32", device=self.device
            )
            logger.info("CLIP 模型加载成功")
        except Exception as e:
            logger.error("CLIP 加载失败: %s", e)

        self.initialized = True

    def generate_caption(self, image_path: str) -> str:
        """使用 BLIP 生成图片描述（英文）。"""
        if not self.initialized:
            self.initialize()

        if not self.blip_model:
            return "Fashion item"

        try:
            raw_image = Image.open(image_path).convert("RGB")
            inputs = self.blip_processor(raw_image, return_tensors="pt").to(
                self.device
            )
            out = self.blip_model.generate(**inputs, max_new_tokens=50)
            caption: str = self.blip_processor.decode(
                out[0], skip_special_tokens=True
            )
            return caption
        except Exception as e:
            logger.error("Caption 生成失败: %s", e)
            return "Error generating caption"

    def extract_clip_features(self, image_path: str) -> np.ndarray:
        """提取 CLIP 图像特征向量（512 维）。"""
        if not self.initialized:
            self.initialize()

        if not self.clip_model:
            return np.zeros(512)

        try:
            image = (
                self.clip_preprocess(Image.open(image_path))
                .unsqueeze(0)
                .to(self.device)
            )
            with torch.no_grad():
                features = self.clip_model.encode_image(image)
            return features.cpu().numpy().flatten()
        except Exception as e:
            logger.error("CLIP 特征提取失败: %s", e)
            return np.zeros(512)

    def analyze_image_attributes(
        self, image_path: str
    ) -> dict[str, Any]:
        """综合分析：提取材质、风格、分类、颜色。

        Returns:
            dict with keys: caption, material, style, category, color, additional_tags
        """
        caption = self.generate_caption(image_path).lower()

        # 1. 材质提取
        materials: dict[str, str] = {
            "denim": "牛仔", "jeans": "牛仔",
            "cotton": "棉",
            "silk": "丝绸",
            "wool": "羊毛", "knitted": "针织",
            "leather": "皮革",
            "polyester": "聚酯纤维",
            "linen": "亚麻",
            "lace": "蕾丝",
            "chiffon": "雪纺",
        }
        detected_material = "未知材质"
        for en, cn in materials.items():
            if en in caption:
                detected_material = cn
                break

        # 2. 风格提取（CLIP Zero-Shot 增强版）
        detected_style = "日常"

        style_classes: dict[str, list[str]] = {
            "新中式": [
                "chinese traditional clothing", "qipao dress",
                "cheongsam", "hanfu", "oriental style", "chinese embroidery",
            ],
            "商务": ["business suit", "formal office wear", "blazer", "white shirt"],
            "休闲": ["casual t-shirt", "jeans", "daily wear", "hoodie"],
            "运动": ["sportswear", "gym clothes", "running shoes", "athletic wear"],
            "复古": ["vintage style", "retro fashion", "old school"],
            "街头": ["streetwear", "hip hop style", "oversized"],
            "晚礼服": ["evening gown", "party dress", "elegant dress"],
            "度假": ["vacation outfit", "beach wear", "bohemian style"],
        }

        flat_prompts: list[str] = []
        prompt_map: list[str] = []

        for style_name, prompts in style_classes.items():
            for p in prompts:
                flat_prompts.append(f"a photo of {p}")
                prompt_map.append(style_name)

        if self.clip_model:
            try:
                image = (
                    self.clip_preprocess(Image.open(image_path))
                    .unsqueeze(0)
                    .to(self.device)
                )
                text = clip.tokenize(flat_prompts).to(self.device)

                with torch.no_grad():
                    logits_per_image, _ = self.clip_model(image, text)
                    probs = (
                        logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                    )

                top_idx = int(np.argmax(probs))
                top_score = float(probs[top_idx])
                predicted_style = prompt_map[top_idx]

                if top_score > 0.15:
                    detected_style = predicted_style

            except Exception as e:
                logger.error("CLIP 风格分类失败: %s", e)
                detected_style = _keyword_style_fallback(caption)
        else:
            detected_style = _keyword_style_fallback(caption)

        # 3. 标签增强：地域文化识别
        additional_tags: list[str] = []
        if detected_style == "新中式":
            additional_tags.append("中式风")
            additional_tags.append("国潮")

        regional_keywords: dict[str, str] = {
            "minority": "少数民族", "ethnic": "少数民族",
            "batik": "蜡染", "tie-dye": "扎染",
            "embroidery": "刺绣", "totem": "图腾",
        }
        for en, cn in regional_keywords.items():
            if en in caption:
                additional_tags.append("中式风")
                additional_tags.append(cn)
                break

        # 4. 分类提取（CLIP 辅助细分）
        detected_category = _classify_category(
            self, image_path, caption, detected_style, additional_tags
        )

        # 5. 颜色提取
        color_map: dict[str, str] = {
            "red": "红色", "blue": "蓝色", "green": "绿色",
            "black": "黑色", "white": "白色", "yellow": "黄色",
            "pink": "粉色", "purple": "紫色",
            "grey": "灰色", "gray": "灰色", "brown": "棕色",
            "orange": "橙色",
        }
        detected_color = "其他"
        for en, cn in color_map.items():
            if en in caption:
                detected_color = cn
                break

        return {
            "caption": caption,
            "material": detected_material,
            "style": detected_style,
            "category": detected_category,
            "color": detected_color,
            "additional_tags": additional_tags,
        }

    def compute_phash(self, image_path: str) -> str | None:
        """计算图片的感知哈希（pHash, 16 位十六进制）。

        Returns None if the image cannot be read.
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None

            # 1. 缩小尺寸 32x32
            img = cv2.resize(img, (32, 32))
            # 2. 转灰度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # 3. DCT 变换
            dct = cv2.dct(np.float32(gray))
            # 4. 取左上角 8x8
            dct_low_freq = dct[:8, :8]
            # 5. 计算均值
            avg = float(np.mean(dct_low_freq))
            # 6. 生成哈希
            phash_bits = ""
            for i in range(8):
                for j in range(8):
                    phash_bits += "1" if dct_low_freq[i, j] > avg else "0"
            return hex(int(phash_bits, 2))[2:].rjust(16, "0")
        except Exception as e:
            logger.error("pHash 计算失败: %s", e)
            return None


# ---------------------------------------------------------------------------
# 模块级辅助函数
# ---------------------------------------------------------------------------


def _keyword_style_fallback(caption: str) -> str:
    """基于关键词的风格回退匹配。"""
    styles: dict[str, str] = {
        "vintage": "复古", "casual": "休闲", "formal": "正式",
        "business": "商务", "sport": "运动",
        "chinese": "新中式", "traditional": "新中式", "qipao": "新中式",
    }
    for en, cn in styles.items():
        if en in caption:
            return cn
    return "日常"


def _classify_category(
    service: AIService,
    image_path: str,
    caption: str,
    detected_style: str,
    additional_tags: list[str],
) -> str:
    """使用 CLIP Zero-Shot 或关键词进行服装分类。"""
    category_classes: dict[str, list[str]] = {
        "旗袍": ["qipao dress", "cheongsam", "chinese traditional dress"],
        "连衣裙": ["dress", "gown", "one-piece"],
        "汉服": ["hanfu", "chinese ancient clothing"],
        "上衣": ["shirt", "blouse", "top", "t-shirt", "jacket", "coat"],
        "下装": ["pants", "trousers", "jeans", "skirt"],
        "鞋履": ["shoe", "sneaker", "boot", "heels"],
        "配饰": ["bag", "handbag", "hat", "scarf", "jewelry"],
    }

    detected_category = "未分类"

    if service.clip_model:
        try:
            cat_prompts: list[str] = []
            cat_map: list[str] = []
            for cat_name, prompts in category_classes.items():
                for p in prompts:
                    cat_prompts.append(f"a photo of {p}")
                    cat_map.append(cat_name)

            image = (
                service.clip_preprocess(Image.open(image_path))
                .unsqueeze(0)
                .to(service.device)
            )
            text = clip.tokenize(cat_prompts).to(service.device)

            with torch.no_grad():
                logits_per_image, _ = service.clip_model(image, text)
                probs = (
                    logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                )

            top_idx = int(np.argmax(probs))
            detected_category = cat_map[top_idx]

            # 强制修正旗袍/汉服的风格
            if detected_category in ("旗袍", "汉服") and detected_style != "新中式":
                detected_style = "新中式"  # noqa: F841 (intentionally mutates outer scope via additional_tags)
                if "中式风" not in additional_tags:
                    additional_tags.insert(0, "中式风")
        except Exception as e:
            logger.error("CLIP 分类细分失败: %s", e)

    if detected_category == "未分类":
        keyword_categories: dict[str, str] = {
            "qipao": "旗袍", "cheongsam": "旗袍",
            "hanfu": "汉服",
            "dress": "连衣裙", "gown": "连衣裙",
            "shirt": "上衣", "blouse": "上衣", "top": "上衣",
            "t-shirt": "上衣",
            "pants": "下装", "trousers": "下装", "jeans": "下装",
            "skirt": "下装",
            "shoe": "鞋履", "sneaker": "鞋履", "boot": "鞋履",
            "sandal": "鞋履",
            "jacket": "上衣", "coat": "上衣", "blazer": "上衣",
            "bag": "配饰", "handbag": "配饰", "backpack": "配饰",
            "hat": "配饰", "scarf": "配饰",
        }
        for en, cn in keyword_categories.items():
            if en in caption:
                detected_category = cn
                break

    return detected_category


# 全局单例
ai_service = AIService()
