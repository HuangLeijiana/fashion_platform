from flask import Blueprint, request, jsonify, current_app
import time

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/track', methods=['POST'])
def track_event():
    if not current_app.config.get('FEATURE_ANALYTICS_EVENTS', True):
        return jsonify({"success": False, "message": "Analytics disabled"}), 403
    try:
        data = request.get_json(force=True) or {}
        event = data.get('event') or 'unknown_event'
        payload = data.get('payload') or {}
        user_ip = request.remote_addr
        ua = request.headers.get('User-Agent', '')
        ts = int(time.time() * 1000)
        current_app.logger.info(f"event={event} ts={ts} ip={user_ip} ua={ua} payload={payload}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": f"Track failed: {str(e)}"}), 500
