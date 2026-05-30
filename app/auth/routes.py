"""认证路由 — 登录、注册、密码重置、个人资料。"""

from __future__ import annotations

import logging
from urllib.parse import urlparse, urljoin

from flask import (
    render_template, redirect, url_for, flash, request, jsonify, session,
    Response as FlaskResponse,
)
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message

from app.extensions import db, mail
from app.models import User, UserProfile
from app.auth.forms import (
    LoginForm, RegistrationForm, ResetPasswordRequestForm,
    ResetPasswordForm, ProfileForm,
)
from . import auth_bp

logger = logging.getLogger(__name__)


def _is_safe_url(target: str | None) -> bool:
    """验证重定向 URL 是否安全（同源检查）。"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target or ""))
    return (
        test_url.scheme in ("http", "https")
        and ref_url.netloc == test_url.netloc
    )


def _wants_json_response() -> bool:
    """检测客户端是否期望 JSON 响应。"""
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True

    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return (
        best == "application/json"
        and request.accept_mimetypes[best]
        >= request.accept_mimetypes["text/html"]
    )


def _get_post_login_target() -> str:
    """获取登录后的重定向目标 URL。"""
    next_page = request.args.get("next")
    if next_page and _is_safe_url(next_page):
        return next_page
    return url_for("main.index")


def _login_error(message: str, status_code: int = 401) -> FlaskResponse:
    """返回登录错误（JSON 或 HTML 重定向）。"""
    if _wants_json_response():
        return jsonify({"success": False, "error": message}), status_code
    flash(message, "error")
    return redirect(url_for("auth.login"))


def _clear_auth_session() -> None:
    """清除 session 中的认证信息。"""
    session.pop("user", None)
    session.pop("username", None)


def _logout_current_session() -> None:
    """登出当前用户并清除 session。"""
    logout_user()
    _clear_auth_session()


# ===============================================================
# 🔹 登录 / 登出
# ===============================================================


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> FlaskResponse:
    if current_user.is_authenticated:
        return redirect(_get_post_login_target())

    form = LoginForm()
    if form.validate_on_submit():
        login_identifier: str = form.username.data.strip()
        user = User.query.filter(
            (User.username == login_identifier) | (User.email == login_identifier)
        ).first()

        if user is None or not user.check_password(form.password.data):
            return _login_error("用户名或密码无效")

        if not user.is_active:
            return _login_error("账户已被禁用", status_code=403)

        login_user(user, remember=form.remember_me.data)
        session["user"] = user.id
        session["username"] = user.username or user.email.split("@")[0]

        redirect_target = _get_post_login_target()
        if _wants_json_response():
            return jsonify({
                "success": True,
                "message": "登录成功",
                "redirect": redirect_target,
            }), 200
        return redirect(redirect_target)

    return render_template("auth/login.html", title="登录", form=form)


@auth_bp.route("/logout")
def logout() -> FlaskResponse:
    _logout_current_session()
    flash("您已成功退出登录。", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/api/logout", methods=["POST"])
@login_required
def api_logout() -> FlaskResponse:
    _logout_current_session()
    return jsonify({"message": "退出登录成功"}), 200


# ===============================================================
# 🔹 注册
# ===============================================================


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> FlaskResponse:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        if request.is_json:
            data: dict[str, str] = request.get_json() or {}
        else:
            data = {
                "username": request.form.get("username", "").strip(),
                "email": request.form.get("email", "").strip().lower(),
                "password": request.form.get("password", ""),
                "confirm_password": request.form.get("confirm_password", ""),
            }

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", password)

        if not username or not email or not password:
            return _register_error("用户名、邮箱和密码不能为空")

        if "@" not in email:
            return _register_error("邮箱格式不正确")

        if password != confirm_password:
            return _register_error("两次输入的密码不一致")

        if len(password) < 6:
            return _register_error("密码长度至少为6位")

        if User.query.filter_by(email=email).first():
            return _register_error("该邮箱已被注册")

        if User.query.filter_by(username=username).first():
            return _register_error("用户名已被使用")

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.exception("注册失败")
            return _register_error(f"注册失败: {exc}", status_code=500)

        if request.is_json:
            return jsonify({
                "message": "注册成功",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            }), 201

        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    form = RegistrationForm()
    return render_template("auth/register.html", title="注册", form=form)


def _register_error(message: str, status_code: int = 400) -> FlaskResponse:
    """返回注册错误（JSON 或 HTML）。"""
    if request.is_json:
        return jsonify({"error": message}), status_code
    flash(message, "error")
    form = RegistrationForm()
    return render_template(
        "auth/register.html", title="注册", form=form
    ), status_code


# ===============================================================
# 🔹 密码重置
# ===============================================================


@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request() -> FlaskResponse:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(user.email, reset_url)

        flash("如果该邮箱已注册，重置密码的说明已发送到您的邮箱。", "info")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password_request.html", title="重置密码", form=form
    )


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token: str) -> FlaskResponse:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user = User.verify_reset_token(token)
    if not user:
        flash("无效或过期的重置链接。", "error")
        return redirect(url_for("auth.reset_password_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        flash("您的密码已更新，现在可以登录了。", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html", title="设置新密码", form=form
    )


def send_password_reset_email(email: str, reset_url: str) -> None:
    """发送密码重置邮件。"""
    try:
        msg = Message(
            subject="重置您的密码 - 云想衣裳",
            recipients=[email],
            html=render_template("email/reset_password.html", reset_url=reset_url),
            body=render_template("email/reset_password.txt", reset_url=reset_url),
        )
        mail.send(msg)
    except Exception:
        logger.exception("发送密码重置邮件失败")


# ===============================================================
# 🔹 个人资料
# ===============================================================


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile() -> FlaskResponse:
    form = ProfileForm()

    profile_obj = UserProfile.query.get(current_user.id)
    if not profile_obj:
        profile_obj = UserProfile(
            user_id=current_user.id,
            username=current_user.username or current_user.email,
        )
        db.session.add(profile_obj)
        db.session.commit()

    if form.validate_on_submit():
        profile_obj.height = form.height.data
        profile_obj.weight = form.weight.data
        profile_obj.age = form.age.data
        profile_obj.gender = form.gender.data
        profile_obj.body_shape = form.body_shape.data
        profile_obj.skin_tone = form.skin_tone.data
        db.session.commit()
        flash("您的个人资料已更新。", "success")
        return redirect(url_for("auth.profile"))

    if request.method == "GET":
        form.height.data = profile_obj.height
        form.weight.data = profile_obj.weight
        form.age.data = profile_obj.age
        form.gender.data = profile_obj.gender or "未设置"
        form.body_shape.data = profile_obj.body_shape or "未设置"
        form.skin_tone.data = profile_obj.skin_tone or "未设置"

    return render_template("auth/profile.html", title="个人资料", form=form)


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user() -> FlaskResponse:
    """返回当前登录用户信息（JSON API）。"""
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "permissions": [],
        }
    })
