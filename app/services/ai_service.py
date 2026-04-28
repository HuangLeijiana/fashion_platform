import os
import torch
import clip
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import cv2
import numpy as np
from flask import current_app

class AIService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.clip_model = None
            cls._instance.blip_model = None
            cls._instance.clip_preprocess = None
            cls._instance.blip_processor = None
            cls._instance.device = "cpu"
        return cls._instance
    
    def initialize(self):
        if self.initialized:
            return
            
        print("[AI Service] 初始化模型...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 1. 加载 BLIP
        # 动态获取项目根目录 (假设 ai_service.py 在 app/services 下)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        
        self.local_blip_path = os.path.join(project_root, "app", "models", "blip-image-captioning-base")
        self.blip_processor = None
        self.blip_model = None
        
        try:
            if os.path.exists(self.local_blip_path):
                self.blip_processor = BlipProcessor.from_pretrained(self.local_blip_path)
                self.blip_model = BlipForConditionalGeneration.from_pretrained(self.local_blip_path).to(self.device)
                
                # 尝试加载自定义微调权重
                model_path = os.path.join(project_root, "app", "checkpoints", "fashion_model.pth")
                if os.path.exists(model_path):
                    checkpoint = torch.load(model_path, map_location=self.device)
                    state_dict = checkpoint.get("blip_model", checkpoint)
                    self.blip_model.load_state_dict(state_dict, strict=False)
                    print("[AI Service] ✅ 加载 BLIP 微调权重成功")
                
                self.blip_model.eval()
            else:
                print(f"[AI Service] ⚠️ BLIP 模型路径不存在: {self.local_blip_path}")
        except Exception as e:
            print(f"[AI Service] ❌ BLIP 加载失败: {e}")

        # 2. 加载 CLIP
        self.clip_model = None
        self.clip_preprocess = None
        try:
            self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
            print("[AI Service] ✅ CLIP 模型加载成功")
        except Exception as e:
            print(f"[AI Service] ❌ CLIP 加载失败: {e}")
            
        self.initialized = True

    def generate_caption(self, image_path):
        """生成图片描述"""
        if not self.initialized:
            self.initialize()
            
        if not self.blip_model:
            return "Fashion item"
            
        try:
            raw_image = Image.open(image_path).convert('RGB')
            inputs = self.blip_processor(raw_image, return_tensors="pt").to(self.device)
            out = self.blip_model.generate(**inputs, max_new_tokens=50)
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            print(f"[AI Service] Caption 生成失败: {e}")
            return "Error generating caption"

    def extract_clip_features(self, image_path):
        """提取 CLIP 特征"""
        if not self.initialized:
            self.initialize()
            
        if not self.clip_model:
            return np.zeros(512)
            
        try:
            image = self.clip_preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                features = self.clip_model.encode_image(image)
            return features.cpu().numpy().flatten()
        except Exception as e:
            print(f"[AI Service] CLIP 特征提取失败: {e}")
            return np.zeros(512)

    def analyze_image_attributes(self, image_path):
        """综合分析：提取材质、风格、分类、颜色"""
        caption = self.generate_caption(image_path).lower()
        
        # 1. 材质提取 (基于关键词)
        materials = {
            "denim": "牛仔", "jeans": "牛仔",
            "cotton": "棉",
            "silk": "丝绸",
            "wool": "羊毛", "knitted": "针织",
            "leather": "皮革",
            "polyester": "聚酯纤维",
            "linen": "亚麻",
            "lace": "蕾丝",
            "chiffon": "雪纺"
        }
        detected_material = "未知材质"
        for en, cn in materials.items():
            if en in caption:
                detected_material = cn
                break
                
        # 2. 风格提取 (CLIP Zero-Shot 增强版)
        detected_style = "日常"
        
        # 定义风格类别及其对应的英文提示词
        style_classes = {
            "新中式": ["chinese traditional clothing", "qipao dress", "cheongsam", "hanfu", "oriental style", "chinese embroidery"],
            "商务": ["business suit", "formal office wear", "blazer", "white shirt"],
            "休闲": ["casual t-shirt", "jeans", "daily wear", "hoodie"],
            "运动": ["sportswear", "gym clothes", "running shoes", "athletic wear"],
            "复古": ["vintage style", "retro fashion", "old school"],
            "街头": ["streetwear", "hip hop style", "oversized"],
            "晚礼服": ["evening gown", "party dress", "elegant dress"],
            "度假": ["vacation outfit", "beach wear", "bohemian style"]
        }
        
        # 展平所有提示词用于 CLIP 计算
        flat_prompts = []
        prompt_map = [] # 记录索引对应的风格
        
        for style_name, prompts in style_classes.items():
            for p in prompts:
                flat_prompts.append(f"a photo of {p}")
                prompt_map.append(style_name)
                
        # CLIP 计算概率
        if self.clip_model:
            try:
                image = self.clip_preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
                text = clip.tokenize(flat_prompts).to(self.device)
                
                with torch.no_grad():
                    logits_per_image, _ = self.clip_model(image, text)
                    probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                
                # 获取最高概率的索引
                top_idx = np.argmax(probs)
                top_score = probs[top_idx]
                predicted_style = prompt_map[top_idx]
                
                # 打印调试信息
                # print(f"[AI Debug] Top style: {predicted_style} ({top_score:.2f})")
                
                # 只有置信度足够高时才采纳，或者直接采纳最高值
                if top_score > 0.15: # 阈值可调
                    detected_style = predicted_style
                    
            except Exception as e:
                print(f"[AI Service] CLIP 风格分类失败: {e}")
                # 回退到关键词匹配
                styles = {
                    "vintage": "复古", "casual": "休闲", "formal": "正式", "business": "商务",
                    "sport": "运动", "chinese": "新中式", "traditional": "新中式", "qipao": "新中式"
                }
                for en, cn in styles.items():
                    if en in caption:
                        detected_style = cn
                        break
        else:
            # 没有 CLIP 模型时的回退逻辑
             styles = {
                "vintage": "复古", "casual": "休闲", "formal": "正式", "business": "商务",
                "sport": "运动", "chinese": "新中式", "traditional": "新中式", "qipao": "新中式"
            }
             for en, cn in styles.items():
                if en in caption:
                    detected_style = cn
                    break
        
        # 3. 标签增强：地域文化识别
        # 如果是新中式，自动添加文化标签
        additional_tags = []
        if detected_style == "新中式":
            additional_tags.append("中式风") # 替换“地域文化”为更具体的“中式风”
            additional_tags.append("国潮")
        
        # 地域特征识别
        regional_keywords = {
            "minority": "少数民族", "ethnic": "少数民族", "batik": "蜡染", 
            "tie-dye": "扎染", "embroidery": "刺绣", "totem": "图腾"
        }
        for en, cn in regional_keywords.items():
            if en in caption:
                additional_tags.append("中式风") # 统一使用中式风
                additional_tags.append(cn)
                break
                
        # 4. 分类提取 (增强版：细分旗袍等)
        detected_category = "未分类"
        
        # 优先使用 CLIP 辅助细分分类
        category_classes = {
            "旗袍": ["qipao dress", "cheongsam", "chinese traditional dress"],
            "连衣裙": ["dress", "gown", "one-piece"],
            "汉服": ["hanfu", "chinese ancient clothing"],
            "上衣": ["shirt", "blouse", "top", "t-shirt", "jacket", "coat"],
            "下装": ["pants", "trousers", "jeans", "skirt"],
            "鞋履": ["shoe", "sneaker", "boot", "heels"],
            "配饰": ["bag", "handbag", "hat", "scarf", "jewelry"]
        }
        
        if self.clip_model:
            try:
                # 展平分类提示词
                cat_prompts = []
                cat_map = []
                for cat_name, prompts in category_classes.items():
                    for p in prompts:
                        cat_prompts.append(f"a photo of {p}")
                        cat_map.append(cat_name)
                
                image = self.clip_preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
                text = clip.tokenize(cat_prompts).to(self.device)
                
                with torch.no_grad():
                    logits_per_image, _ = self.clip_model(image, text)
                    probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                
                top_idx = np.argmax(probs)
                detected_category = cat_map[top_idx]
                
                # 如果分类是旗袍/汉服，且风格没识别对，强制修正风格
                if detected_category in ["旗袍", "汉服"] and detected_style != "新中式":
                    detected_style = "新中式"
                    if "中式风" not in additional_tags:
                        additional_tags.insert(0, "中式风")
            except Exception as e:
                print(f"[AI Service] CLIP 分类细分失败: {e}")
                # 回退到关键词逻辑...
                pass
        
        # 如果 CLIP 没跑或者失败，回退到关键词
        if detected_category == "未分类":
            categories = {
                "qipao": "旗袍", "cheongsam": "旗袍", # 关键词优先匹配旗袍
                "hanfu": "汉服",
                "dress": "连衣裙", "gown": "连衣裙",
                "shirt": "上衣", "blouse": "上衣", "top": "上衣", "t-shirt": "上衣",
                "pants": "下装", "trousers": "下装", "jeans": "下装", "skirt": "下装",
                "shoe": "鞋履", "sneaker": "鞋履", "boot": "鞋履", "sandal": "鞋履",
                "jacket": "上衣", "coat": "上衣", "blazer": "上衣",
                "bag": "配饰", "handbag": "配饰", "backpack": "配饰",
                "hat": "配饰", "scarf": "配饰"
            }
            for en, cn in categories.items():
                if en in caption:
                    detected_category = cn
                    break
                
        # 4. 颜色 (保留原有的 extract_dominant_color 逻辑，这里简化调用)
        # 可以结合 caption 中的颜色词
        colors = {
            "red": "红色", "blue": "蓝色", "green": "绿色", "black": "黑色",
            "white": "白色", "yellow": "黄色", "pink": "粉色", "purple": "紫色",
            "grey": "灰色", "gray": "灰色", "brown": "棕色", "orange": "橙色"
        }
        detected_color = "其他"
        for en, cn in colors.items():
            if en in caption:
                detected_color = cn
                break
        
        return {
            "caption": caption,
            "material": detected_material,
            "style": detected_style,
            "category": detected_category,
            "color": detected_color,
            "additional_tags": additional_tags
        }

    def compute_phash(self, image_path):
        """计算感知哈希 (pHash)"""
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
            avg = np.mean(dct_low_freq)
            # 6. 生成哈希
            phash = ""
            for i in range(8):
                for j in range(8):
                    phash += "1" if dct_low_freq[i, j] > avg else "0"
            # 转十六进制字符串
            return hex(int(phash, 2))[2:].rjust(16, '0')
        except Exception as e:
            print(f"[AI Service] pHash 计算失败: {e}")
            return None

# 全局单例
ai_service = AIService()
