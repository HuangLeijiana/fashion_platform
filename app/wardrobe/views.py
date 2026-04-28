import json
import logging
import os

from flask import Blueprint, render_template, request, jsonify, flash, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db, allowed_file, save_uploaded_file, delete_uploaded_file
from app.models import ClothingItem
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

wardrobe_bp = Blueprint('wardrobe', __name__)


def _absolute_static_path(relative_path):
    if not relative_path:
        return None
    return os.path.join(current_app.static_folder, relative_path.replace('/', os.sep))


def _serialize_items(items):
    return [item.to_dict() for item in items]


def _extract_features_safely(image_path):
    try:
        service = AIService()
        features = service.extract_clip_features(image_path)
        return json.dumps(features.tolist())
    except Exception:
        logger.exception('图片特征提取失败')
        return None


@wardrobe_bp.route('/')
@login_required
def wardrobe():
    items = ClothingItem.query.filter_by(user_id=current_user.id).order_by(ClothingItem.created_at.desc()).all()
    return render_template('wardrobe/wardrobe.html', clothing_items=_serialize_items(items))


@wardrobe_bp.route('/add', methods=['POST'])
@login_required
def add_clothing():
    name = (request.form.get('name') or '').strip()
    category = (request.form.get('category') or '').strip()

    if not name or not category:
        return jsonify({'success': False, 'message': '名称和分类不能为空'}), 400

    image_path = None
    feature_vector = None
    file = request.files.get('image')

    if file and file.filename and allowed_file(file.filename):
        image_path = save_uploaded_file(file)
        absolute_path = _absolute_static_path(image_path)
        if absolute_path:
            feature_vector = _extract_features_safely(absolute_path)

    try:
        item = ClothingItem(
            user_id=current_user.id,
            name=name,
            category=category,
            color=request.form.get('color'),
            brand=request.form.get('brand'),
            season=request.form.get('season'),
            occasion=request.form.get('occasion'),
            image_path=image_path,
            feature_vector=feature_vector,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({'success': True, 'message': '添加成功', 'item_id': item.id})
    except Exception as exc:
        db.session.rollback()
        logger.exception('添加衣物失败')
        return jsonify({'success': False, 'message': f'添加失败：{exc}'}), 500


@wardrobe_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_clothing(item_id):
    item = ClothingItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': '物品不存在或无权删除'}), 404

    try:
        old_image_path = item.image_path
        db.session.delete(item)
        db.session.commit()
        delete_uploaded_file(old_image_path)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as exc:
        db.session.rollback()
        logger.exception('删除衣物失败')
        return jsonify({'success': False, 'message': f'删除失败：{exc}'}), 500


@wardrobe_bp.route('/edit/<int:item_id>', methods=['GET'])
@login_required
def get_clothing_item(item_id):
    item = ClothingItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': '物品不存在或无权访问'}), 404
    return jsonify({'success': True, 'item': item.to_dict()})


@wardrobe_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_clothing(item_id):
    item = ClothingItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': '物品不存在或无权编辑'}), 404

    name = (request.form.get('name') or '').strip()
    category = (request.form.get('category') or '').strip()
    if not name or not category:
        return jsonify({'success': False, 'message': '名称和分类不能为空'}), 400

    try:
        item.name = name
        item.category = category
        item.color = request.form.get('color')
        item.brand = request.form.get('brand')
        item.season = request.form.get('season')
        item.occasion = request.form.get('occasion')

        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            old_image_path = item.image_path
            image_path = save_uploaded_file(file)
            item.image_path = image_path
            absolute_path = _absolute_static_path(image_path)
            if absolute_path:
                item.feature_vector = _extract_features_safely(absolute_path)
            delete_uploaded_file(old_image_path)

        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as exc:
        db.session.rollback()
        logger.exception('更新衣物失败')
        return jsonify({'success': False, 'message': f'更新失败：{exc}'}), 500


@wardrobe_bp.route('/search', methods=['GET'])
@login_required
def search_clothing():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    color = request.args.get('color', '').strip()

    if not query and not category and not color:
        return jsonify({'success': False, 'message': '请输入搜索条件'}), 400

    items_query = ClothingItem.query.filter_by(user_id=current_user.id)

    if query:
        like_term = f'%{query}%'
        items_query = items_query.filter(or_(ClothingItem.name.like(like_term), ClothingItem.brand.like(like_term)))
    if category:
        items_query = items_query.filter(ClothingItem.category == category)
    if color:
        items_query = items_query.filter(ClothingItem.color.like(f'%{color}%'))

    items = items_query.order_by(ClothingItem.created_at.desc()).all()
    results = _serialize_items(items)
    return jsonify({'success': True, 'results': results, 'count': len(results)})


@wardrobe_bp.route('/smart_search', methods=['GET'])
@login_required
def smart_search():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': '请输入搜索关键词'}), 400

    like_term = f'%{keyword}%'
    items = ClothingItem.query.filter(
        ClothingItem.user_id == current_user.id,
        or_(
            ClothingItem.name.like(like_term),
            ClothingItem.brand.like(like_term),
            ClothingItem.color.like(like_term),
            ClothingItem.category.like(like_term),
            ClothingItem.season.like(like_term),
            ClothingItem.occasion.like(like_term),
            ClothingItem.style_tags.like(like_term),
        )
    ).order_by(ClothingItem.created_at.desc()).all()

    results = _serialize_items(items)
    return jsonify({'success': True, 'results': results, 'count': len(results)})


@wardrobe_bp.route('/diagnosis', methods=['GET'])
@login_required
def wardrobe_diagnosis():
    items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return jsonify({'success': False, 'message': '衣柜为空，请先添加衣物。'}), 200

    color_count = {}
    category_count = {}
    style_count = {}

    for item in items:
        color = item.color or '未标注'
        category = item.category or '未分类'
        style = item.occasion or '日常'
        color_count[color] = color_count.get(color, 0) + 1
        category_count[category] = category_count.get(category, 0) + 1
        style_count[style] = style_count.get(style, 0) + 1

    suggestions = []
    if category_count.get('裤子', 0) + category_count.get('下装', 0) < 2:
        suggestions.append('下装数量偏少，建议补充黑色、米色或牛仔基础款。')
    if color_count.get('白色', 0) < 1:
        suggestions.append('缺少白色基础款，可提升整体搭配的灵活性。')
    if category_count.get('外套', 0) < 1:
        suggestions.append('外套数量偏少，建议补充轻薄外套和保暖外套。')
    if len(style_count) <= 2:
        suggestions.append('风格较集中，可以尝试加入新风格单品丰富搭配。')
    if not suggestions:
        suggestions.append('衣柜构成较均衡，搭配自由度较高。')

    tops = [item for item in items if item.category in ['上衣', '衬衫', 'T恤', '卫衣', '外套']]
    bottoms = [item for item in items if item.category in ['裤子', '下装', '牛仔裤', '裙子']]

    outfits = []
    for top in tops[:3]:
        for bottom in bottoms[:3]:
            outfits.append({
                'top_name': top.name,
                'bottom_name': bottom.name,
                'top_image': f'/static/{top.image_path}' if top.image_path else None,
                'bottom_image': f'/static/{bottom.image_path}' if bottom.image_path else None,
            })

    return jsonify({
        'success': True,
        'color_distribution': color_count,
        'category_distribution': category_count,
        'style_distribution': style_count,
        'diagnosis': suggestions,
        'outfit_recommendations': outfits[:3],
    })


@wardrobe_bp.route('/api/items', methods=['GET'])
@login_required
def wardrobe_items_api():
    items = ClothingItem.query.filter_by(user_id=current_user.id).order_by(ClothingItem.created_at.desc()).all()
    results = _serialize_items(items)
    return jsonify({'success': True, 'items': results, 'count': len(results)})


@wardrobe_bp.route('/batch_add', methods=['POST'])
@login_required
def batch_add_clothing():
    files = request.files.getlist('images')
    if not files or not files[0].filename:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400

    default_category = request.form.get('category') or '未分类'
    skip_duplicate = request.form.get('skip_duplicate', 'true').lower() == 'true'
    ai_service = AIService()

    existing_hashes = {
        value for (value,) in db.session.query(ClothingItem.image_hash)
        .filter(ClothingItem.user_id == current_user.id, ClothingItem.image_hash.isnot(None))
        .all()
    }

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for file in files:
        if not file or not file.filename or not allowed_file(file.filename):
            failed_count += 1
            continue

        image_path = None
        try:
            image_path = save_uploaded_file(file)
            absolute_path = _absolute_static_path(image_path)
            image_hash = ai_service.compute_phash(absolute_path) if absolute_path else None

            if image_hash and skip_duplicate and image_hash in existing_hashes:
                delete_uploaded_file(image_path)
                skipped_count += 1
                continue

            attrs = ai_service.analyze_image_attributes(absolute_path) if absolute_path else {}
            category = attrs.get('category') or default_category
            if category == '未分类':
                category = default_category

            style_tags = []
            if attrs.get('additional_tags'):
                style_tags.extend(attrs['additional_tags'])
            if attrs.get('style') and attrs['style'] != '日常':
                style_tags.append(attrs['style'])

            item = ClothingItem(
                user_id=current_user.id,
                name=os.path.splitext(file.filename)[0],
                category=category,
                color=attrs.get('color'),
                material=attrs.get('material'),
                occasion=attrs.get('style'),
                image_path=image_path,
                image_hash=image_hash,
                style_tags=','.join(style_tags),
            )
            db.session.add(item)
            if image_hash:
                existing_hashes.add(image_hash)
            success_count += 1
        except Exception:
            logger.exception('批量导入图片失败')
            if image_path:
                delete_uploaded_file(image_path)
            failed_count += 1

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception('批量保存衣物失败')
        return jsonify({'success': False, 'message': f'批量保存失败：{exc}'}), 500

    message = f'成功导入 {success_count} 张'
    if skipped_count:
        message += f'，跳过重复 {skipped_count} 张'
    if failed_count:
        message += f'，失败 {failed_count} 张'

    return jsonify({
        'success': True,
        'message': message,
        'count': success_count,
        'skipped': skipped_count,
        'failed': failed_count,
    })
