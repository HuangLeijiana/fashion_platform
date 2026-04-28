import json
import base64
import logging
import os
import tempfile

from flask import Blueprint, render_template, request, jsonify, session, current_app
from sqlalchemy import or_

from app.extensions import db
from app.models import Product, ClothingItem

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)


def _get_image_searcher():
    """延迟加载图像搜索器，避免在模块导入时失败。"""
    try:
        from app.search.image_search import image_searcher
        return image_searcher
    except Exception:
        logger.warning('图像搜索模块不可用，将返回空结果')
        return None


@search_bp.before_app_request
def init_search_history():
    if 'search_history' not in session:
        session['search_history'] = []
    if 'cart' not in session:
        session['cart'] = {}


@search_bp.route('/')
def search():
    query = (request.args.get('q') or '').strip()
    category = request.args.get('category') or ''
    brand = request.args.get('brand') or ''
    sort_by = request.args.get('sort') or 'relevance'
    wardrobe_only = request.args.get('wardrobe_only', '0') in ('1', 'true', 'True')

    if query:
        history = session.get('search_history', [])
        if query in history:
            history.remove(query)
        history.insert(0, query)
        session['search_history'] = history[:10]
        session.modified = True

    results = []
    wardrobe_results = []

    if query:
        if wardrobe_only:
            wardrobe_results = _perform_wardrobe_search(query, category)
        else:
            results = _perform_product_search(query, category, brand, sort_by)

    brands = _get_brands()
    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values()) if session.get('cart') else 0

    return render_template(
        'search/search.html',
        query=query,
        results=results,
        category=category,
        brand=brand,
        sort_by=sort_by,
        wardrobe_only=wardrobe_only,
        wardrobe_results=wardrobe_results,
        brands=brands,
        search_history=session.get('search_history', []),
        cart_count=cart_count,
    )


def _perform_product_search(query, category='', brand='', sort_by='relevance', page=1, per_page=20):
    """使用 ORM 执行商品搜索。"""
    like_term = f'%{query}%'
    products_query = Product.query.filter(
        or_(Product.name.like(like_term), Product.description.like(like_term), Product.brand.like(like_term))
    )

    if category:
        products_query = products_query.filter(Product.category == category)
    if brand:
        products_query = products_query.filter(Product.brand == brand)

    if sort_by == 'price_asc':
        products_query = products_query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        products_query = products_query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        products_query = products_query.order_by(Product.created_at.desc())
    else:
        products_query = products_query.order_by(Product.name)

    offset = (page - 1) * per_page
    products = products_query.offset(offset).limit(per_page).all()
    return [p.to_dict() for p in products]


def _perform_wardrobe_search(query, category='', page=1, per_page=50):
    """在当前用户衣柜中搜索。"""
    from flask_login import current_user
    user_id = current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else session.get('user', 0)

    like_term = f'%{query}%'
    items_query = ClothingItem.query.filter(
        ClothingItem.user_id == user_id,
        or_(
            ClothingItem.name.like(like_term),
            ClothingItem.brand.like(like_term),
            ClothingItem.color.like(like_term),
            ClothingItem.category.like(like_term),
        ),
    )

    if category:
        items_query = items_query.filter(ClothingItem.category == category)

    color = (request.args.get('color') or '').strip()
    if color:
        items_query = items_query.filter(ClothingItem.color.like(f'%{color}%'))

    offset = (page - 1) * per_page
    items = items_query.order_by(ClothingItem.created_at.desc()).offset(offset).limit(per_page).all()

    results = []
    for item in items:
        image_url = '/static/images/placeholder.jpg'
        if item.image_path:
            normalized = item.image_path.replace('\\', '/')
            if normalized.startswith('uploads/'):
                image_url = f'/static/{normalized}'
            else:
                image_url = f'/static/uploads/{os.path.basename(normalized)}'
        results.append({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'color': item.color,
            'brand': item.brand,
            'season': item.season,
            'occasion': item.occasion,
            'image_path': item.image_path,
            'image_url': image_url,
            'created_at': item.created_at.isoformat() if item.created_at else None,
        })
    return results


def _get_brands():
    try:
        rows = db.session.query(Product.brand).filter(
            Product.brand.isnot(None), Product.brand != ''
        ).distinct().order_by(Product.brand).all()
        return [row[0] for row in rows]
    except Exception:
        logger.exception('获取品牌列表失败')
        return []


# ---------- 购物车接口 ----------
# 注意：当前购物车存储在 session 中，未来应迁移到数据库关联用户。

@search_bp.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400

        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        if not product_id:
            return jsonify({'success': False, 'message': '商品ID不能为空'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': '商品不存在'}), 404

        cart = session.get('cart', {})
        product_key = str(product_id)

        if product_key in cart:
            cart[product_key]['quantity'] += quantity
        else:
            cart[product_key] = {
                'id': product_id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
            }

        session['cart'] = cart
        session.modified = True
        cart_count = sum(item['quantity'] for item in cart.values())
        return jsonify({
            'success': True,
            'message': f'"{product.name}" 已成功加入购物车',
            'cart_count': cart_count,
        })
    except Exception:
        logger.exception('添加购物车失败')
        return jsonify({'success': False, 'message': '添加购物车失败，请重试'}), 500


@search_bp.route('/api/update_cart', methods=['POST'])
def update_cart():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400

        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        if not product_id:
            return jsonify({'success': False, 'message': '商品ID不能为空'}), 400
        if quantity < 1 or quantity > 99:
            return jsonify({'success': False, 'message': '数量必须在 1-99 之间'}), 400

        cart = session.get('cart', {})
        product_key = str(product_id)
        if product_key not in cart:
            return jsonify({'success': False, 'message': '商品不在购物车中'}), 404

        cart[product_key]['quantity'] = quantity
        session['cart'] = cart
        session.modified = True

        cart_items = list(cart.values())
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
        total_quantity = sum(item['quantity'] for item in cart_items)
        item_total = cart[product_key]['price'] * quantity

        return jsonify({
            'success': True,
            'message': '购物车已更新',
            'item_total': item_total,
            'total_amount': total_amount,
            'total_quantity': total_quantity,
        })
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '数量必须是有效数字'}), 400
    except Exception:
        logger.exception('更新购物车失败')
        return jsonify({'success': False, 'message': '更新购物车失败'}), 500


@search_bp.route('/api/remove_from_cart', methods=['POST'])
def remove_from_cart():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400

        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'success': False, 'message': '商品ID不能为空'}), 400

        cart = session.get('cart', {})
        product_key = str(product_id)
        if product_key not in cart:
            return jsonify({'success': False, 'message': '商品不在购物车中'}), 404

        removed = cart.pop(product_key)
        session['cart'] = cart
        session.modified = True

        cart_items = list(cart.values())
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
        total_quantity = sum(item['quantity'] for item in cart_items)

        return jsonify({
            'success': True,
            'message': f'"{removed["name"]}" 已从购物车移除',
            'total_amount': total_amount,
            'total_quantity': total_quantity,
        })
    except Exception:
        logger.exception('移除购物车商品失败')
        return jsonify({'success': False, 'message': '移除商品失败'}), 500


@search_bp.route('/api/clear_cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    session.modified = True
    return jsonify({'success': True, 'message': '购物车已清空', 'total_amount': 0, 'total_quantity': 0})


@search_bp.route('/api/get_cart_count')
def get_cart_count():
    cart = session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    return jsonify({'success': True, 'cart_count': cart_count})


@search_bp.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = list(cart.values())
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    total_quantity = sum(item['quantity'] for item in cart_items)
    return render_template(
        'search/cart.html',
        cart_items=cart_items,
        total_amount=total_amount,
        total_quantity=total_quantity,
        cart_count=total_quantity,
    )


# ---------- 搜索历史 ----------

@search_bp.route('/api/clear_search_history', methods=['POST'])
def clear_search_history():
    session.pop('search_history', None)
    session.modified = True
    return jsonify({'success': True, 'message': '搜索历史已清除'})


@search_bp.route('/api/get_search_history')
def get_search_history():
    return jsonify({'success': True, 'search_history': session.get('search_history', [])})


# ---------- 搜索建议 ----------

@search_bp.route('/api/suggestions')
def search_suggestions():
    query = (request.args.get('q') or '').strip()
    if not query:
        return jsonify({'success': False, 'suggestions': []})

    like_term = f'%{query}%'
    try:
        rows = db.session.query(Product.name).filter(Product.name.like(like_term)).limit(8).all()
        suggestions = list({row[0] for row in rows if row[0]})
        return jsonify({'success': True, 'suggestions': suggestions[:8]})
    except Exception:
        logger.exception('搜索建议失败')
        return jsonify({'success': False, 'suggestions': []})


# ---------- 衣柜 API 搜索 ----------

@search_bp.route('/api/wardrobe', methods=['GET'])
def wardrobe_api_search():
    if not current_app.config.get('FEATURE_SEARCH_WARDROBE_API', True):
        return jsonify({'success': False, 'message': '衣柜搜索API已关闭'}), 403

    query = (request.args.get('q') or '').strip()
    category = (request.args.get('category') or '').strip()
    page = int(request.args.get('page') or '1')
    per_page = int(request.args.get('per_page') or '50')

    try:
        items = _perform_wardrobe_search(query, category, page, per_page)
        return jsonify({'success': True, 'results': items, 'count': len(items)})
    except Exception as exc:
        logger.exception('衣柜搜索失败')
        return jsonify({'success': False, 'message': f'搜索失败：{exc}'}), 500


# ---------- 图像搜索 ----------

@search_bp.route('/api/search_by_image', methods=['POST'])
def search_by_image():
    searcher = _get_image_searcher()
    if searcher is None:
        return jsonify({'success': False, 'message': '图像搜索功能暂不可用'}), 503

    temp_path = None
    try:
        if 'image' in request.files:
            image_file = request.files['image']
            if not image_file or not image_file.filename:
                return jsonify({'success': False, 'message': '请选择图片'}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                image_file.save(tmp.name)
                temp_path = tmp.name
        else:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'success': False, 'message': '请求数据为空'}), 400

            image_data = data.get('image_data', '')
            if not image_data:
                return jsonify({'success': False, 'message': '图片数据为空'}), 400

            if ',' in image_data:
                image_data = image_data.split(',')[1]

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(base64.b64decode(image_data))
                temp_path = tmp.name

        results = searcher.search_similar_products(temp_path, top_k=12)

        for result in results:
            if 'similarity_percent' not in result:
                score = result.get('similarity_score', 0)
                result['similarity_percent'] = round(score * 100, 2)
            if 'similarity_score' not in result and 'similarity_percent' in result:
                result['similarity_score'] = result['similarity_percent'] / 100.0

            images = result.get('images')
            if isinstance(images, str):
                try:
                    images = json.loads(images)
                except (json.JSONDecodeError, TypeError):
                    images = [images] if images else []
                result['images'] = images
            elif not isinstance(images, list):
                result['images'] = []

            for i, img_path in enumerate(result['images']):
                if img_path and not img_path.startswith(('http', '/static')):
                    result['images'][i] = f'/static/images/products/{img_path}'

        return jsonify({
            'success': True,
            'results': results,
            'message': f'找到 {len(results)} 个相似商品',
        })
    except Exception as exc:
        logger.exception('图像搜索失败')
        return jsonify({'success': False, 'message': f'图像搜索失败：{exc}'}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@search_bp.route('/image_search')
def image_search_page():
    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())
    return render_template('search/image_search.html', cart_count=cart_count)
