# app/extensions.py
import os
import logging
from werkzeug.utils import secure_filename
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail

logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """验证文件是否符合上传格式"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, subfolder=''):
    """安全保存上传的文件"""
    if file and allowed_file(file.filename):
        import uuid
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"

        if subfolder:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        else:
            upload_dir = current_app.config['UPLOAD_FOLDER']

        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        if subfolder:
            return os.path.join('uploads', subfolder, filename)
        else:
            return os.path.join('uploads', filename)
    return None


def delete_uploaded_file(filepath):
    """删除上传的文件"""
    try:
        if filepath:
            absolute_path = os.path.join(current_app.static_folder, filepath)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
                return True
    except Exception as e:
        logger.error("删除文件失败: %s", e)
    return False
