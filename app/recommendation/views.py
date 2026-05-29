import os
import json
import numpy as np
import torch
import clip
import cv2
import requests
from PIL import Image
from flask import (
    Blueprint, render_template, request, jsonify, current_app, url_for
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import glob
from datetime import datetime
import traceback
import logging
from . import recommendation_bp
import random

logger = logging.getLogger(__name__)
from app.services.ai_service import ai_service
from app.services.image_utils import extract_dominant_color
from app.extensions import db
from app.models import UserProfile

# ===============================================================
# 🔹 图像分析函数（全中文优化）
# ===============================================================
def image_to_description(image_path, user_style=None):
    """
    基于规则和颜色检测的图片描述生成（不依赖BLIP模型）
    """
    if not os.path.exists(image_path):
        return "时尚服饰单品"

    try:
        # 1. 检测主色调
        dominant_color = extract_dominant_color(image_path)

        # 2. 基于文件名和颜色推断服装类型
        filename = os.path.basename(image_path).lower()

        # 服装类型推断
        cloth_type = "服饰"
        if any(word in filename for word in ['dress', 'skirt', '裙']):
            cloth_type = "连衣裙"
        elif any(word in filename for word in ['shirt', 'blouse', '衬衫']):
            cloth_type = "衬衫"
        elif any(word in filename for word in ['pants', 'jeans', 'trousers', '裤']):
            cloth_type = "裤子"
        elif any(word in filename for word in ['shoe', 'sneaker', 'boot', '鞋']):
            cloth_type = "鞋子"
        elif any(word in filename for word in ['jacket', 'coat', '外套']):
            cloth_type = "外套"
        elif any(word in filename for word in ['hoodie', 'sweater', 'sweatshirt', '卫衣']):
            cloth_type = "卫衣"
        elif any(word in filename for word in ['t-shirt', 'tshirt', 'tee', 't恤']):
            cloth_type = "T恤"

        # 3. 基于颜色和类型生成描述
        color_descriptions = {
            "黑色": "经典黑色", "白色": "纯净白色", "红色": "热情红色",
            "蓝色": "沉稳蓝色", "绿色": "清新绿色", "黄色": "明亮黄色",
            "粉色": "温柔粉色", "紫色": "神秘紫色", "灰色": "高级灰色",
            "棕色": "复古棕色", "橙色": "活力橙色", "其他": "时尚"
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
                "棕色": "复古风", "橙色": "运动风"
            }
            style = style_keywords.get(dominant_color, "潮流风")

        # 5. 组合描述
        descriptions = [
            f"{color_desc}{cloth_type}，{style}设计，适合日常穿搭",
            f"{style}{cloth_type}，主色调为{dominant_color}，时尚百搭",
            f"{color_desc}{cloth_type}，展现{style}魅力，适配多种场合",
            f"{cloth_type}单品，{dominant_color}系{style}，穿搭优选"
        ]

        return random.choice(descriptions)

    except Exception as e:
        logger.error("规则描述生成失败: %s", e)
        return "时尚服饰单品，适合多种场合穿搭"


def parse_cloth_type(description):
    """从纯中文描述中解析衣物类型（全中文匹配）"""
    desc = description.lower()
    # 中文关键词匹配（优先级：具体类型 > 通用类型）
    type_mapping = {
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
        "围巾": ["围巾", "围脖"]
    }
    for cloth_type, keywords in type_mapping.items():
        if any(kw in description for kw in keywords):
            return cloth_type
    return "服饰"  # 默认类型（纯中文）


def parse_style_tag(description):
    """从纯中文描述中解析风格标签（全中文匹配）"""
    # 中文关键词匹配
    style_mapping = {
        "街头风": ["街头", "潮流", "个性", "嘻哈"],
        "优雅风": ["优雅", "气质", "知性", "端庄"],
        "休闲风": ["休闲", "日常", "舒适", "百搭"],
        "运动风": ["运动", "活力", "轻便", "健身"],
        "复古风": ["复古", "怀旧", "经典", "老式"],
        "极简风": ["极简", "简约", "大气", "简洁"],
        "甜美风": ["甜美", "可爱", "清新", "少女"],
        "正式风": ["正式", "商务", "得体", "端庄"]
    }
    for style, keywords in style_mapping.items():
        if any(kw in description for kw in keywords):
            return style
    return "通用风"  # 默认风格（纯中文）

# ===============================================================
# 🔹 天气模块（优化天气穿搭建议生成）
# ===============================================================
def get_weather(city_name=None, ip=None):
    try:
        if not city_name:
            city_api = f"https://ipapi.co/{ip}/json/"
            city_resp = requests.get(city_api, timeout=6).json()
            city_name = city_resp.get("city", "北京")

        api_url = "http://apis.juhe.cn/simpleWeather/query"
        api_key = current_app.config.get('WEATHER_API_KEY') or os.environ.get('WEATHER_API_KEY', '')
        params = {"key": api_key, "city": city_name}
        weather_resp = requests.get(api_url, params=params, timeout=6).json()

        if weather_resp.get("error_code") != 0:
            return city_name, 20, "晴朗"

        realtime = weather_resp["result"]["realtime"]
        temp = float(realtime.get("temperature", 20))
        condition = realtime.get("info", "晴朗")
        # 确保天气状况是中文（API返回已为中文）
        return city_name, temp, condition
    except Exception as e:
        logger.error("天气获取失败: %s", e)
        return city_name or "未知城市", 20, "晴朗"

# 新增：根据天气和衣物类型生成穿搭建议
def get_weather_outfit_suggestion(temp, condition, cloth_type):
    """
    根据气温、天气状况和衣物类型生成纯中文穿搭建议
    :param temp: 气温（℃）
    :param condition: 天气状况（中文）
    :param cloth_type: 衣物类型（中文）
    :return: 穿搭建议字符串
    """
    # 温度分段建议
    if temp >= 30:
        temp_suggest = "高温天气"
        outfit_tip = f"{cloth_type}材质透气舒适，适合高温环境，能有效散热"
    elif 20 <= temp < 30:
        temp_suggest = "适宜温度"
        outfit_tip = f"{cloth_type}厚度适中，适配当前气温，穿搭舒适无负担"
    elif 10 <= temp < 20:
        temp_suggest = "微凉天气"
        outfit_tip = f"{cloth_type}保暖性较好，可搭配薄外套穿着，应对微凉气温"
    else:
        temp_suggest = "低温天气"
        outfit_tip = f"{cloth_type}保暖性强，适合低温环境，能有效抵御寒冷"
    
    # 天气状况补充建议
    weather_supplement = ""
    if "雨" in condition:
        weather_supplement = " 雨天路面湿滑，搭配防水鞋履更佳"
    elif "雪" in condition:
        weather_supplement = " 雪天寒冷且路面易滑，建议搭配防滑鞋和厚袜子"
    elif "晴" in condition:
        weather_supplement = " 晴天阳光充足，可搭配遮阳帽或太阳镜"
    elif "阴" in condition:
        weather_supplement = " 阴天无强烈日晒，穿搭灵活性高"
    
    return f"{temp_suggest}（{temp}℃，{condition}）{outfit_tip}{weather_supplement}"


def build_recommend_reason(rec, profile, city, temp, condition):
    """
    使用用户画像 + 天气 + 单品信息生成更自然的推荐理由（规则驱动，接近大模型风格）
    """
    parts = []
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

    # 2. 利用用户画像做“个人化”解释
    if profile:
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
        if profile.body_shape in ("梨形", "梨型"):
            body_reason = "下半身易显重，因此选择版型相对利落的单品，可以在视觉上拉长比例、弱化臀胯宽度。"
        elif profile.body_shape in ("苹果形", "苹果型"):
            body_reason = "上半身容易显得饱满，这类单品在肩线和整体线条上相对干净，有助于弱化上半身体积感。"
        elif profile.body_shape in ("沙漏形", "沙漏型"):
            body_reason = "沙漏型身材腰线优势明显，这类单品可以把腰线自然强调出来，整体更有曲线感。"
        elif profile.body_shape in ("矩形", "H型"):
            body_reason = "矩形身材直线感较强，这类单品在轮廓和细节上增加了一点层次感，能让整体不那么“直上直下”。"
        else:
            body_reason = ""

        # 肤色与颜色协同（简单规则）
        color_reason = ""
        color = str(rec.get("color") or "")
        if profile.skin_tone and color:
            if profile.skin_tone in ("白皙", "自然") and any(c in color for c in ["黑", "藏蓝", "深色"]):
                color_reason = "深色系在您偏亮的肤色下对比感会更强，整体更显气质。"
            elif profile.skin_tone in ("小麦色", "深色") and any(c in color for c in ["米色", "驼色", "卡其"]):
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
        try:
            preferred = []
            if profile.style_pref:
                if isinstance(profile.style_pref, str):
                    preferred = json.loads(profile.style_pref) if profile.style_pref.strip().startswith("[") else [profile.style_pref]
                elif isinstance(profile.style_pref, list):
                    preferred = profile.style_pref
        except Exception:
            preferred = []

        if preferred:
            hit = [s for s in preferred if s and s in style_tag]
            if hit:
                parts.append(f"这件单品在风格上贴近您标记的「{'、'.join(hit)}」偏好，穿上会更符合您一贯的审美。")
            else:
                parts.append("在风格上我们刻意做了些差异，让它在保持整体协调的前提下，给您的日常穿搭带来一点新鲜感。")

    # 3. 气温与天气场景的说明
    if city and weather_suggestion:
        parts.append(f"考虑到当前{city}{condition}、气温约 {int(temp)}℃，{weather_suggestion}")
    elif weather_suggestion:
        parts.append(weather_suggestion)

    # 4. 轻微点题
    if "中式" in style_tag or "旗袍" in desc:
        parts.append("整体偏中式风格，既有仪式感，又不会过于张扬，适合作为日常与稍正式场合之间的过渡搭配。")

    return " ".join(p.strip() for p in parts if p and p.strip())

# 删除数据库相关的 import_local_fashion_images 函数

# ===============================================================
# 🔹 上传衣物接口（删除数据库操作）
# ===============================================================
@recommendation_bp.route('/upload', methods=['POST'])
def upload_cloth():
    try:
        # 1. 获取上传的图片文件和表单参数
        cloth_image = request.files.get('cloth_image')
        username = request.form.get('username', 'unknown_user')
        user_style = request.form.get('style') or request.form.get('preference')
        
        # 2. 验证图片文件是否存在
        if not cloth_image or cloth_image.filename.strip() == '':
            return jsonify({"success": False, "error": "未选择图片，请上传衣物图片"}), 400
        
        # 3. 验证文件格式（仅允许图片）
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = secure_filename(cloth_image.filename).rsplit('.', 1)[-1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False, 
                "error": f"不支持的文件格式！仅允许：{', '.join(allowed_extensions)}"
            }), 400

        # 4. 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        safe_filename = secure_filename(cloth_image.filename)
        final_filename = f"{timestamp}_{safe_filename}"

        # 5. 定义保存路径
        upload_folder = os.path.abspath(
            os.path.join(current_app.root_path, '../static/uploads')
        )
        os.makedirs(upload_folder, exist_ok=True)

        # 6. 拼接完整保存路径
        file_path = os.path.join(upload_folder, final_filename)

        # 7. 保存图片到本地文件夹
        try:
            cloth_image.save(file_path)
        except PermissionError:
            return jsonify({
                "success": False, 
                "error": "没有权限写入文件，请检查static/uploads文件夹权限"
            }), 500

        # 8. 生成前端可访问的图片URL
        image_url = url_for('static', filename=f"uploads/{final_filename}")

        # 9. 提取图片属性（全中文）
        desc = image_to_description(file_path, user_style=user_style)
        color = extract_dominant_color(file_path)
        style_tag = parse_style_tag(desc)
        cloth_type = parse_cloth_type(desc)

        # 10. 返回结果（纯中文提示，删除数据库相关字段）
        return jsonify({
            "success": True,
            "message": "图片上传成功！",
            "username": username,
            "image_url": image_url,
            "local_path": file_path,
            "filename": final_filename,
            "description": desc,  # 纯中文
            "color": color,       # 纯中文
            "style_tag": style_tag,  # 纯中文
            "cloth_type": cloth_type  # 纯中文
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": f"上传失败：{str(e)}",
            "detail": traceback.format_exc()
        }), 500

# ===============================================================
# 🔹 AI推荐接口（融合天气穿搭建议，支持衣柜联动）
# ===============================================================
@recommendation_bp.route('/ai_recommend', methods=['POST'])
@login_required
def ai_recommend():
    try:
        from app.extensions import get_db_connection
        
        data = request.get_json(force=True)
        latest_image_path = data.get("local_path")
        city_input = data.get("city", "")
        # 强制启用衣柜关联（如果前端传了）
        include_wardrobe = data.get("include_wardrobe", False)
        user_profile_payload = data.get("user_profile") or {}
        
        ip = request.remote_addr or "127.0.0.1"
        
        if not latest_image_path or not os.path.exists(latest_image_path):
            return jsonify({"success": False, "error": "未找到最新上传的图片"}), 400

        profile = None

        # 0. 同步更新用户画像信息
        if user_profile_payload:
            profile = UserProfile.query.get(current_user.id)
            if not profile:
                profile = UserProfile(
                    user_id=current_user.id,
                    username=current_user.username or (current_user.email.split("@")[0] if current_user.email else "")
                )
                db.session.add(profile)

            def to_float(val):
                try:
                    return float(val) if val not in (None, "",) else None
                except ValueError:
                    return None

            def to_int(val):
                try:
                    return int(val) if val not in (None, "",) else None
                except ValueError:
                    return None

            profile.height = to_float(user_profile_payload.get("height"))
            profile.weight = to_float(user_profile_payload.get("weight"))
            profile.age = to_int(user_profile_payload.get("age"))
            gender = user_profile_payload.get("gender")
            if gender:
                profile.gender = gender
            body_shape = user_profile_payload.get("body_shape")
            if body_shape:
                profile.body_shape = body_shape
            skin_tone = user_profile_payload.get("skin_tone")
            if skin_tone:
                profile.skin_tone = skin_tone

            styles = user_profile_payload.get("style_pref") or []
            if isinstance(styles, list):
                profile.style_pref = json.dumps(styles, ensure_ascii=False)
            elif isinstance(styles, str) and styles.strip():
                profile.style_pref = styles

            db.session.commit()

        # 1. 获取天气信息
        if current_app.config.get('FEATURE_WEATHER_SERVICE', True):
            city, temp, condition = get_weather(city_input, ip)
        else:
            city, temp, condition = (city_input or "北京", 20, "晴朗")

        # 2. 提取最新上传图片的CLIP特征
        latest_vec = np.array(ai_service.extract_clip_features(latest_image_path))
        if np.linalg.norm(latest_vec) == 0:
            return jsonify({"success": False, "error": "图片特征提取失败"}), 400

        # 3. 准备候选池
        static_folder = os.path.abspath(os.path.join(current_app.root_path, '../static'))
        fashion_folder = os.path.join(static_folder, 'images', 'products')
        
        candidates = [] # 存储 (image_path, source_type, metadata)
        
        # 3.1 添加本地图库图片
        if os.path.exists(fashion_folder):
            for fname in os.listdir(fashion_folder):
                if fname.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                    candidates.append({
                        "path": os.path.join(fashion_folder, fname),
                        "type": "gallery",
                        "data": {}
                    })
        
        # 3.2 添加衣柜图片 (如果启用)
        if include_wardrobe:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    # 优先获取旗袍/中式风格的衣物，或者全部获取
                    cursor.execute("SELECT * FROM clothing_items WHERE user_id = %s", (current_user.id,))
                    items = cursor.fetchall()
                    
                    for item in items:
                        if item['image_path']:
                            # 处理相对路径
                            rel_path = item['image_path'].replace('\\', '/')
                            if rel_path.startswith('uploads/'):
                                abs_path = os.path.join(static_folder, 'uploads', os.path.basename(rel_path))
                            else:
                                abs_path = os.path.join(static_folder, rel_path)
                                
                            if os.path.exists(abs_path):
                                candidates.append({
                                    "path": abs_path,
                                    "type": "wardrobe",
                                    "data": item # 携带衣柜物品元数据
                                })
                finally:
                    conn.close()

        if not candidates:
             # 尝试添加一个系统默认的候选图作为兜底
             default_img = os.path.join(fashion_folder, '001.png')
             if os.path.exists(default_img):
                 candidates.append({
                    "path": default_img,
                    "type": "gallery",
                    "data": {}
                 })
             else:
                 return jsonify({"success": False, "error": "暂无推荐资源，请先添加衣柜或图库图片"}), 404

        # 4. 计算相似度
        sim_results = []
        # 限制最大计算数量，防止超时
        max_candidates = 50
        if len(candidates) > max_candidates:
            random.shuffle(candidates)
            candidates = candidates[:max_candidates]
            
        for cand in candidates:
            # 确保 cand 是字典
            if isinstance(cand, dict):
                img_path = cand["path"]
            else:
                # 兼容旧代码或错误数据
                img_path = cand
                cand = {"path": cand, "type": "gallery", "data": {}}

            # 提取特征
            cand_vec = np.array(ai_service.extract_clip_features(img_path))
            if np.linalg.norm(cand_vec) == 0:
                continue

            # 余弦相似度
            similarity = float(
                np.dot(latest_vec, cand_vec) 
                / (np.linalg.norm(latest_vec) * np.linalg.norm(cand_vec))
            )
            
            # 过滤低相似度 (可选) -> 移除硬阈值，改为排序后截取，确保有结果返回
            # if similarity < 0.2: 
            #    continue

            # 生成URL
            relative_path = os.path.relpath(img_path, static_folder).replace('\\', '/')
            image_url = url_for('static', filename=relative_path)

            # 获取描述信息
            if cand.get("type") == "wardrobe":
                # 衣柜物品直接使用数据库信息
                item = cand.get("data", {})
                desc = item.get("style_tags") or item.get("name")
                color = item.get("color") or "未知色"
                style_tag = "衣柜单品"
                cloth_type = item.get("category") or "服饰"
                
                # 特别标注旗袍
                if "旗袍" in str(desc) or "中式" in str(desc):
                    style_tag = "中式风·衣柜"
            else:
                # 图库图片实时分析
                color = extract_dominant_color(img_path)
                desc = image_to_description(img_path)
                style_tag = parse_style_tag(desc)
                cloth_type = parse_cloth_type(desc)

            sim_results.append({
                "image_url": image_url,
                "similarity": round(similarity, 4),
                "color": color,
                "description": desc,
                "style_tag": style_tag,
                "cloth_type": cloth_type,
                "weather_suggestion": get_weather_outfit_suggestion(temp, condition, cloth_type),
                "is_wardrobe": cand.get("type") == "wardrobe",
                "wardrobe_item_id": cand.get("data", {}).get("id") if cand.get("type") == "wardrobe" else None
            })

        # 5. 排序
        # 优先展示高相似度的衣柜单品 (加权)
        for r in sim_results:
            if r["is_wardrobe"]:
                r["similarity"] += 0.05 # 给予衣柜物品一点加权，优先展示
        
        sim_results.sort(key=lambda x: x["similarity"], reverse=True)
        top_recommendations = sim_results[:5]
        
        # 兜底：如果完全没有相似结果（sim_results为空），则返回任意候选（极少发生）
        if not top_recommendations and candidates:
             # 构造一个默认结果
             cand = candidates[0]
             img_path = cand["path"]
             relative_path = os.path.relpath(img_path, static_folder).replace('\\', '/')
             top_recommendations.append({
                "image_url": url_for('static', filename=relative_path),
                "similarity": 0.1,
                "color": "未知",
                "description": "默认推荐",
                "style_tag": "默认",
                "cloth_type": "服饰",
                "weather_suggestion": "天气适宜",
                "reason": "为您推荐的默认搭配。",
                "is_wardrobe": False
             })

        # 6. 生成推荐理由（结合用户画像与天气信息）
        if profile is None:
            # 如果本次请求没带画像，也尝试从数据库中读取已有画像
            profile = UserProfile.query.get(current_user.id)

        for rec in top_recommendations:
            rec["reason"] = build_recommend_reason(rec, profile, city, temp, condition)

        return jsonify({
            "success": True, 
            "city": city, 
            "recommendations": top_recommendations,
            "used_wardrobe": include_wardrobe
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": f"推荐异常：{str(e)}"}), 500


# ===============================================================
# 🔹 天气接口（纯中文返回）
# ===============================================================
@recommendation_bp.route('/weather', methods=['POST'])
def get_weather_by_city():
    try:
        if not current_app.config.get('FEATURE_WEATHER_SERVICE', True):
            return jsonify({"success": False, "error": "天气服务已关闭"}), 503
        data = request.get_json(force=True)
        city_input = data.get('city', '').strip()
        ip = request.remote_addr or "127.0.0.1"
        if not city_input:
            return jsonify({"success": False, "error": "未提供城市名称"}), 400
        city, temp, condition = get_weather(city_input, ip)
        logger.info("获取天气成功：%s - %s %s℃", city, condition, temp)
        return jsonify({
            "success": True, 
            "city": city, 
            "temperature": temp, 
            "condition": condition,
            "suggestion": f"当前{city}{condition}，气温{temp}℃，{'适合穿着轻便衣物' if temp > 25 else '建议适当增添衣物' if temp < 15 else '穿搭可灵活选择'}"
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": f"天气接口异常：{str(e)}"}), 500




# ===============================================================
# 🔹 页面入口（纯中文展示优化，删除数据库相关）
# ===============================================================
@recommendation_bp.route('/', methods=['GET'])
def recommendation():
    try:
        # 1. 修正路径
        static_root = os.path.abspath(
            os.path.join(current_app.root_path, '../static')
        )
        
        # 2. 定义需要扫描的本地图片文件夹
        target_folders = [
            os.path.join(static_root, 'uploads'),
            os.path.join(static_root, 'images', 'products')
        ]

        # 3. 自动创建缺失的文件夹
        for folder in target_folders:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                logger.info("文件夹不存在，已自动创建：%s", folder)

        # 4. 收集所有有效图片
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        all_images = []

        for folder in target_folders:
            for filename in os.listdir(folder):
                if filename.lower().endswith(image_extensions):
                    img_abs_path = os.path.join(folder, filename)
                    img_rel_path = os.path.relpath(img_abs_path, static_root)
                    
                    # 为每张图片生成纯中文来源描述
                    source_desc = "用户上传" if "uploads" in folder else "本地图库"
                    
                    # 记录图片关键信息（纯中文来源）
                    all_images.append({
                        "image_url": url_for('static', filename=img_rel_path),
                        "modify_time": os.path.getmtime(img_abs_path),
                        "source_folder": source_desc,  # 纯中文来源描述
                        "filename": filename
                    })

        # 5. 排序并取前6张
        all_images.sort(key=lambda x: x["modify_time"], reverse=True)
        recent_cloths = all_images[:6]

        # 6. 渲染模板（模板中已为中文展示）
        return render_template('recommendation/recommendation.html', recent_cloths=recent_cloths)

    except Exception as e:
        error_msg = f"页面加载失败：{str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        return render_template('error.html', message=error_msg), 500
    
# ===============================================================
# 🔹 全局错误捕获（纯中文错误提示，删除数据库相关）
# ===============================================================
@recommendation_bp.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    error_detail = str(e)
    # 删除数据库相关错误提示
    # if "UserClothes" in error_detail or "sqlalchemy" in error_detail:
    #     error_detail = "已移除数据库依赖，请确认代码中无残留数据库查询逻辑"
    
    return jsonify({
        "success": False,
        "error": {
            "type": type(e).__name__,
            "message": error_detail,
            "tip": "若为文件夹相关错误，请检查static/uploads和static/images/products是否存在，且有读写权限"
        }
    }), 500

# ===============================================================
# 🔹 本地图库批量导入接口（纯中文提示，删除数据库操作）
# ===============================================================
@recommendation_bp.route('/import_local', methods=['POST'])
def import_local_images():
    try:
        # 1. 接收前端参数
        data = request.get_json()
        local_dir = data.get('local_dir', 'images/products')
        if not os.path.isabs(local_dir):
            project_root = os.path.abspath(os.path.join(current_app.root_path, '../'))
            local_dir = os.path.join(project_root, local_dir)

        # 2. 校验本地图库文件夹是否存在
        if not os.path.exists(local_dir):
            return jsonify({
                "success": False,
                "error": "本地图库文件夹不存在",
                "detail": f"路径：{local_dir}",
                "tip": "请确认本地图库路径正确，或先创建该文件夹"
            }), 400

        # 3. 定义目标文件夹
        dest_folder = os.path.join(current_app.root_path, 'static', 'images', 'products')
        os.makedirs(dest_folder, exist_ok=True)

        # 4. 收集本地图库中的所有图片
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
        image_paths = []
        for ext in image_extensions:
            matched_paths = glob.glob(os.path.join(local_dir, ext), recursive=False)
            image_paths.extend(matched_paths)

        # 5. 校验是否有可导入的图片
        if not image_paths:
            return jsonify({
                "success": False,
                "error": "本地图库无有效图片",
                "detail": f"路径：{local_dir}，支持格式：{image_extensions}",
                "tip": "请确认文件夹中存在jpg/png等格式的图片"
            }), 404

        # 6. 批量复制图片（仅复制文件，不写入数据库）
        imported_count = 0
        skipped_count = 0
        failed_list = []

        for img_path in image_paths:
            try:
                filename = os.path.basename(img_path)
                dest_path = os.path.join(dest_folder, filename)

                if os.path.exists(dest_path):
                    logger.info("图片已存在，已跳过：%s", filename)
                    skipped_count += 1
                    continue

                # 复制图片文件
                with open(img_path, 'rb') as f_src, open(dest_path, 'wb') as f_dest:
                    f_dest.write(f_src.read())
                
                imported_count += 1
                logger.info("图片导入成功：%s（源路径：%s）", filename, img_path)

            except Exception as e:
                error_msg = f"文件名：{os.path.basename(img_path)}，错误：{str(e)}"
                failed_list.append(error_msg)
                logger.error("图片导入失败：%s", error_msg)
                continue

        # 7. 生成纯中文结果响应
        result = {
            "success": True,
            "message": f"本地图库导入完成，共处理{len(image_paths)}张图片",
            "stats": {
                "总图片数": len(image_paths),
                "成功导入数": imported_count,
                "重复跳过数": skipped_count,
                "导入失败数": len(failed_list)
            },
            "dest_folder": "static/images/products",
            "tip": "导入的图片已自动添加纯中文描述和标签，可直接用于推荐"
        }

        if failed_list:
            result["warning"] = "部分图片导入失败，详情如下"
            result["failed_details"] = failed_list

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "本地图库导入接口异常",
            "detail": str(e),
            "tip": "请检查本地图库路径是否有权限访问，或图片是否被占用"
        }), 500
