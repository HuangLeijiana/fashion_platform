import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/fashion-advisor')
def fashion_advisor_page():
    return render_template('fashion_advisor/fashion_advisor.html')


@main_bp.route('/account/settings')
@login_required
def account_settings():
    return render_template('account/settings.html')


@main_bp.route('/account/update', methods=['POST'])
@login_required
def update_account():
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip()

    if username:
        current_user.username = username
    if email:
        current_user.email = email

    try:
        db.session.commit()
        flash('账户信息更新成功。', 'success')
    except Exception as exc:
        db.session.rollback()
        logger.exception('更新账户信息失败')
        flash(f'更新失败：{exc}', 'danger')

    return redirect(url_for('main.account_settings'))


@main_bp.route('/account/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([current_password, new_password, confirm_password]):
            flash('请填写所有字段。', 'danger')
            return render_template('account/change_password.html')

        if not current_user.check_password(current_password):
            flash('当前密码不正确。', 'danger')
            return render_template('account/change_password.html')

        if len(new_password) < 8:
            flash('新密码长度至少为 8 位。', 'danger')
            return render_template('account/change_password.html')

        if not any(char.isdigit() for char in new_password) or not any(char.isalpha() for char in new_password):
            flash('新密码必须同时包含字母和数字。', 'danger')
            return render_template('account/change_password.html')

        if new_password != confirm_password:
            flash('两次输入的新密码不一致。', 'danger')
            return render_template('account/change_password.html')

        if current_user.check_password(new_password):
            flash('新密码不能与当前密码相同。', 'danger')
            return render_template('account/change_password.html')

        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功。', 'success')
            return redirect(url_for('main.account_settings'))
        except Exception:
            db.session.rollback()
            logger.exception('修改密码失败')
            flash('密码修改失败，请稍后重试。', 'danger')

    return render_template('account/change_password.html')


@main_bp.route('/account/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    if request.method == 'POST':
        flash('通知设置已保存。', 'success')
        return redirect(url_for('main.account_settings'))
    return render_template('account/notifications.html')


@main_bp.route('/account/privacy', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    if request.method == 'POST':
        flash('隐私设置已保存。', 'success')
        return redirect(url_for('main.account_settings'))
    return render_template('account/privacy.html')
