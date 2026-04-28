import logging

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.extensions import get_db_connection

logger = logging.getLogger(__name__)

fashion_advisor_bp = Blueprint('fashion_advisor', __name__, url_prefix='/fashion-advisor')


def get_advisor_service():
    from app.fashion_advisor.services import FashionAdvisorService
    return FashionAdvisorService()


advisor_service = get_advisor_service()


@fashion_advisor_bp.route('/')
def index():
    return render_template('fashion_advisor/fashion_advisor.html')


@fashion_advisor_bp.route('/api/health', methods=['GET'])
def health_check():
    try:
        result = advisor_service.health_check()
        return jsonify(result)
    except Exception as exc:
        logger.exception('健康检查失败')
        return jsonify({'error': f'服务异常：{exc}'}), 500


@fashion_advisor_bp.route('/api/advice', methods=['POST'])
def get_advice():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400

        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({'error': '消息不能为空'}), 400

        logger.info('收到用户消息：%s', message)
        result = advisor_service.get_fashion_advice(message)
        return jsonify(result)
    except Exception as exc:
        logger.exception('获取时尚建议失败')
        return jsonify({'error': f'处理请求时出错：{exc}'}), 500


@fashion_advisor_bp.route('/api/reset', methods=['POST'])
def reset_conversation():
    try:
        result = advisor_service.reset_conversation()
        return jsonify(result)
    except Exception as exc:
        logger.exception('重置对话失败')
        return jsonify({'error': f'重置对话失败：{exc}'}), 500
