"""推荐蓝图路由处理器 — 图片上传、AI推荐、天气查询、图库管理。"""

import os
import glob
import json
import logging
import traceback

import numpy as np
from flask import (
    Blueprint, render_template, request, jsonify, current_app, url_for,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

from . import recommendation_bp
from .analyzer import image_to_description, parse_cloth_type, parse_style_tag
from .weather import get_weather, get_weather_outfit_suggestion
from .reasoning import build_recommend_reason
from app.services.ai_service import ai_service
from app.services.image_utils import extract_dominant_color
from app.extensions import db
from app.models import UserProfile

logger = logging.getLogger(__name__)


# ===============================================================
# 🔹 上传衣物接口
# ===============================================================
@recommendation_bp.route("/upload", methods=["POST"])
def upload_cloth():
    try:
        cloth_image = request.files.get("cloth_image")
        username = request.form.get("username", "unknown_user")
        user_style = request.form.get("style") or request.form.get("preference")

        if not cloth_image or cloth_image.filename.strip() == "":
            return jsonify({"success": False, "error": "未选择图片，请上传衣物图片"}), 400

        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        file_ext = secure_filename(cloth_image.filename).rsplit(".", 1)[-1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False,
                "error": f"不支持的文件格式！仅允许：{', '.join(allowed_extensions)}",
            }), 400

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        safe_filename = secure_filename(cloth_image.filename)
        final_filename = f"{timestamp}_{safe_filename}"

        upload_folder = os.path.abspath(
            os.path.join(current_app.root_path, "../static/uploads")
        )
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, final_filename)

        try:
            cloth_image.save(file_path)
        except PermissionError:
            return jsonify({
                "success": False,
                "error": "没有权限写入文件，请检查static/uploads文件夹权限",
            }), 500

        image_url = url_for("static", filename=f"uploads/{final_filename}")

        desc = image_to_description(file_path, user_style=user_style)
        color = extract_dominant_color(file_path)
        style_tag = parse_style_tag(desc)
        cloth_type = parse_cloth_type(desc)

        return jsonify({
            "success": True,
            "message": "图片上传成功！",
            "username": username,
            "image_url": image_url,
            "local_path": file_path,
            "filename": final_filename,
            "description": desc,
            "color": color,
            "style_tag": style_tag,
            "cloth_type": cloth_type,
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"上传失败：{str(e)}",
            "detail": traceback.format_exc(),
        }), 500


# ===============================================================
# 🔹 AI推荐接口（融合天气穿搭建议，支持衣柜联动）
# ===============================================================
@recommendation_bp.route("/ai_recommend", methods=["POST"])
@login_required
def ai_recommend():
    try:
        data = request.get_json(force=True)
        latest_image_path = data.get("local_path")
        city_input = data.get("city", "")
        include_wardrobe = data.get("include_wardrobe", False)
        user_profile_payload = data.get("user_profile") or {}

        ip = request.remote_addr or "127.0.0.1"

        if not latest_image_path or not os.path.exists(latest_image_path):
            return jsonify({"success": False, "error": "未找到最新上传的图片"}), 400

        profile = None

        # 0. 同步更新用户画像信息
        if user_profile_payload:
            profile = _sync_user_profile(current_user, user_profile_payload)

        # 1. 获取天气信息
        if current_app.config.get("FEATURE_WEATHER_SERVICE", True):
            city, temp, condition = get_weather(city_input, ip)
        else:
            city, temp, condition = (city_input or "北京", 20, "晴朗")

        # 2. 提取最新上传图片的CLIP特征
        latest_vec = np.array(ai_service.extract_clip_features(latest_image_path))
        if np.linalg.norm(latest_vec) == 0:
            return jsonify({"success": False, "error": "图片特征提取失败"}), 400

        # 3. 准备候选池
        static_folder = os.path.abspath(
            os.path.join(current_app.root_path, "../static")
        )
        candidates = _build_candidate_pool(
            static_folder, include_wardrobe, current_user.id
        )

        if not candidates:
            return jsonify({
                "success": False,
                "error": "暂无推荐资源，请先添加衣柜或图库图片",
            }), 404

        # 4. 计算相似度并排序
        top_recommendations = _compute_similarities(
            latest_vec, candidates, static_folder, temp, condition
        )

        # 5. 为每个推荐生成推荐理由
        if profile is None:
            profile = UserProfile.query.get(current_user.id)

        for rec in top_recommendations:
            rec["reason"] = build_recommend_reason(
                rec, profile, city, temp, condition
            )

        return jsonify({
            "success": True,
            "city": city,
            "recommendations": top_recommendations,
            "used_wardrobe": include_wardrobe,
        })

    except Exception as e:
        import traceback as tb
        tb.print_exc()
        return jsonify({"success": False, "error": f"推荐异常：{str(e)}"}), 500


# ===============================================================
# 🔹 天气接口
# ===============================================================
@recommendation_bp.route("/weather", methods=["POST"])
def get_weather_by_city():
    try:
        if not current_app.config.get("FEATURE_WEATHER_SERVICE", True):
            return jsonify({"success": False, "error": "天气服务已关闭"}), 503

        data = request.get_json(force=True)
        city_input = data.get("city", "").strip()
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
            "suggestion": (
                f"当前{city}{condition}，气温{temp}℃，"
                f"{'适合穿着轻便衣物' if temp > 25 else '建议适当增添衣物' if temp < 15 else '穿搭可灵活选择'}"
            ),
        })
    except Exception as e:
        import traceback as tb
        tb.print_exc()
        return jsonify({"success": False, "error": f"天气接口异常：{str(e)}"}), 500


# ===============================================================
# 🔹 页面入口
# ===============================================================
@recommendation_bp.route("/", methods=["GET"])
def recommendation():
    try:
        static_root = os.path.abspath(
            os.path.join(current_app.root_path, "../static")
        )

        target_folders = [
            os.path.join(static_root, "uploads"),
            os.path.join(static_root, "images", "products"),
        ]

        for folder in target_folders:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                logger.info("文件夹不存在，已自动创建：%s", folder)

        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        all_images = []

        for folder in target_folders:
            for filename in os.listdir(folder):
                if filename.lower().endswith(image_extensions):
                    img_abs_path = os.path.join(folder, filename)
                    img_rel_path = os.path.relpath(img_abs_path, static_root)

                    source_desc = "用户上传" if "uploads" in folder else "本地图库"

                    all_images.append({
                        "image_url": url_for("static", filename=img_rel_path),
                        "modify_time": os.path.getmtime(img_abs_path),
                        "source_folder": source_desc,
                        "filename": filename,
                    })

        all_images.sort(key=lambda x: x["modify_time"], reverse=True)
        recent_cloths = all_images[:6]

        return render_template(
            "recommendation/recommendation.html", recent_cloths=recent_cloths
        )

    except Exception as e:
        error_msg = f"页面加载失败：{str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        return render_template("error.html", message=error_msg), 500


# ===============================================================
# 🔹 全局错误捕获
# ===============================================================
@recommendation_bp.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return jsonify({
        "success": False,
        "error": {
            "type": type(e).__name__,
            "message": str(e),
            "tip": "若为文件夹相关错误，请检查static/uploads和static/images/products是否存在，且有读写权限",
        },
    }), 500


# ===============================================================
# 🔹 本地图库批量导入接口
# ===============================================================
@recommendation_bp.route("/import_local", methods=["POST"])
def import_local_images():
    try:
        data = request.get_json()
        local_dir = data.get("local_dir", "images/products")
        if not os.path.isabs(local_dir):
            project_root = os.path.abspath(
                os.path.join(current_app.root_path, "../")
            )
            local_dir = os.path.join(project_root, local_dir)

        if not os.path.exists(local_dir):
            return jsonify({
                "success": False,
                "error": "本地图库文件夹不存在",
                "detail": f"路径：{local_dir}",
                "tip": "请确认本地图库路径正确，或先创建该文件夹",
            }), 400

        dest_folder = os.path.join(
            current_app.root_path, "static", "images", "products"
        )
        os.makedirs(dest_folder, exist_ok=True)

        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"]
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(glob.glob(os.path.join(local_dir, ext)))

        if not image_paths:
            return jsonify({
                "success": False,
                "error": "本地图库无有效图片",
                "detail": f"路径：{local_dir}，支持格式：{image_extensions}",
                "tip": "请确认文件夹中存在jpg/png等格式的图片",
            }), 404

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

                with open(img_path, "rb") as f_src, open(dest_path, "wb") as f_dest:
                    f_dest.write(f_src.read())

                imported_count += 1
                logger.info("图片导入成功：%s（源路径：%s）", filename, img_path)

            except Exception as e:
                error_msg = f"文件名：{os.path.basename(img_path)}，错误：{str(e)}"
                failed_list.append(error_msg)
                logger.error("图片导入失败：%s", error_msg)
                continue

        result = {
            "success": True,
            "message": f"本地图库导入完成，共处理{len(image_paths)}张图片",
            "stats": {
                "总图片数": len(image_paths),
                "成功导入数": imported_count,
                "重复跳过数": skipped_count,
                "导入失败数": len(failed_list),
            },
            "dest_folder": "static/images/products",
            "tip": "导入的图片已自动添加纯中文描述和标签，可直接用于推荐",
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
            "tip": "请检查本地图库路径是否有权限访问，或图片是否被占用",
        }), 500


# ===============================================================
# 🔹 辅助函数
# ===============================================================


def _sync_user_profile(current_user, user_profile_payload: dict):
    """同步用户画像到数据库，返回更新后的 profile 对象。"""
    profile = UserProfile.query.get(current_user.id)
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            username=(
                current_user.username
                or (current_user.email.split("@")[0] if current_user.email else "")
            ),
        )
        db.session.add(profile)

    def _to_float(val):
        try:
            return float(val) if val not in (None, "",) else None
        except (ValueError, TypeError):
            return None

    def _to_int(val):
        try:
            return int(val) if val not in (None, "",) else None
        except (ValueError, TypeError):
            return None

    profile.height = _to_float(user_profile_payload.get("height"))
    profile.weight = _to_float(user_profile_payload.get("weight"))
    profile.age = _to_int(user_profile_payload.get("age"))

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
    return profile


def _build_candidate_pool(
    static_folder: str, include_wardrobe: bool, user_id: str
) -> list[dict]:
    """构建推荐候选池（本地图库 + 可选衣柜）。"""
    from app.models import ClothingItem

    candidates: list[dict] = []

    # 本地图库
    fashion_folder = os.path.join(static_folder, "images", "products")
    if os.path.exists(fashion_folder):
        for fname in os.listdir(fashion_folder):
            if fname.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
                candidates.append({
                    "path": os.path.join(fashion_folder, fname),
                    "type": "gallery",
                    "data": {},
                })

    # 衣柜图片 — 使用 SQLAlchemy ORM
    if include_wardrobe:
        clothing_items = ClothingItem.query.filter_by(user_id=user_id).all()
        for item in clothing_items:
            if item.image_path:
                rel_path = item.image_path.replace("\\", "/")
                if rel_path.startswith("uploads/"):
                    abs_path = os.path.join(
                        static_folder, "uploads", os.path.basename(rel_path)
                    )
                else:
                    abs_path = os.path.join(static_folder, rel_path)

                if os.path.exists(abs_path):
                    candidates.append({
                        "path": abs_path,
                        "type": "wardrobe",
                        "data": item,  # ORM 对象，在 _compute_similarities 中处理
                    })

    return candidates


def _compute_similarities(
    latest_vec, candidates: list[dict], static_folder: str, temp: float, condition: str
) -> list[dict]:
    """计算候选图片与上传图片的CLIP余弦相似度并排序返回前5。"""
    import random

    max_candidates = 50
    if len(candidates) > max_candidates:
        random.shuffle(candidates)
        candidates = candidates[:max_candidates]

    sim_results = []
    for cand in candidates:
        img_path = cand["path"]

        cand_vec = np.array(ai_service.extract_clip_features(img_path))
        if np.linalg.norm(cand_vec) == 0:
            continue

        similarity = float(
            np.dot(latest_vec, cand_vec)
            / (np.linalg.norm(latest_vec) * np.linalg.norm(cand_vec))
        )

        relative_path = os.path.relpath(img_path, static_folder).replace("\\", "/")
        image_url = url_for("static", filename=relative_path)

        if cand.get("type") == "wardrobe":
            item = cand.get("data")  # SQLAlchemy ClothingItem ORM 对象
            desc = item.style_tags or item.name
            color = item.color or "未知色"
            style_tag = "衣柜单品"
            cloth_type = item.category or "服饰"
            if "旗袍" in str(desc) or "中式" in str(desc):
                style_tag = "中式风·衣柜"
        else:
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
            "weather_suggestion": get_weather_outfit_suggestion(
                temp, condition, cloth_type
            ),
            "is_wardrobe": cand.get("type") == "wardrobe",
            "wardrobe_item_id": (
                item.id
                if cand.get("type") == "wardrobe"
                else None
            ),
        })

    # 衣柜单品加权
    for r in sim_results:
        if r["is_wardrobe"]:
            r["similarity"] += 0.05

    sim_results.sort(key=lambda x: x["similarity"], reverse=True)
    top = sim_results[:5]

    # 兜底
    if not top and candidates:
        cand = candidates[0]
        img_path = cand["path"]
        relative_path = os.path.relpath(img_path, static_folder).replace("\\", "/")
        top.append({
            "image_url": url_for("static", filename=relative_path),
            "similarity": 0.1,
            "color": "未知",
            "description": "默认推荐",
            "style_tag": "默认",
            "cloth_type": "服饰",
            "weather_suggestion": "天气适宜",
            "reason": "为您推荐的默认搭配。",
            "is_wardrobe": False,
        })

    return top
