import uuid
import json
import secrets
import logging
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

logger = logging.getLogger(__name__)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    user_profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    clothes = db.relationship('UserClothes', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_administrator(self):
        return self.is_admin

    def generate_reset_token(self, expires_in=3600):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.commit()
        return self.reset_token

    @staticmethod
    def verify_reset_token(token):
        user = User.query.filter_by(reset_token=token).first()
        if user and user.reset_token_expiration > datetime.utcnow():
            return user
        return None

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiration = None
        db.session.commit()


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    user_id = db.Column(db.CHAR(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

    body_shape = db.Column(db.String(50))
    skin_tone = db.Column(db.String(50))
    style_pref = db.Column(db.Text, default='[]')
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))

    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())


class UserClothes(db.Model):
    __tablename__ = 'user_clothes'

    cloth_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.CHAR(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    cloth_type = db.Column(db.String(50), nullable=False)
    feature_vector = db.Column(db.Text)
    color = db.Column(db.String(50))
    style_tag = db.Column(db.String(50))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))

    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())


class ClothingItem(db.Model):
    """衣柜服装项 - SQLAlchemy ORM 模型，替代原有原生SQL操作"""
    __tablename__ = 'clothing_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100))
    color = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    season = db.Column(db.String(50))
    occasion = db.Column(db.String(100))
    material = db.Column(db.String(100))
    image_path = db.Column(db.Text)
    image_hash = db.Column(db.String(64))
    feature_vector = db.Column(db.Text)
    style_tags = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    @staticmethod
    def get_by_user(user_id):
        return ClothingItem.query.filter_by(user_id=user_id).order_by(ClothingItem.created_at.desc()).all()

    def to_dict(self):
        import os as _os
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'category': self.category,
            'subcategory': self.subcategory,
            'color': self.color,
            'brand': self.brand,
            'season': self.season,
            'occasion': self.occasion,
            'material': self.material,
            'image_path': self.image_path,
            'style_tags': self.style_tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if data.get('image_path'):
            base = _os.path.basename(data['image_path'].replace('\\', '/'))
            data['image_path'] = f"uploads/{base}"
        return data


class Product(db.Model):
    """商品模型 - 用于搜索模块"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False, default=0.0)
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    images = db.Column(db.Text)
    attributes = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0.0,
            'category': self.category,
            'brand': self.brand,
            'images': [],
            'attributes': {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if self.images:
            try:
                imgs = json.loads(self.images)
                for i, img_path in enumerate(imgs):
                    if not img_path.startswith(('http', '/static')):
                        imgs[i] = f'/static/images/products/{img_path}'
                    elif img_path.startswith('/static/products/'):
                        imgs[i] = img_path.replace('/static/products/', '/static/images/products/')
                data['images'] = imgs
            except (json.JSONDecodeError, TypeError):
                data['images'] = []

        if self.attributes:
            try:
                data['attributes'] = json.loads(self.attributes)
            except (json.JSONDecodeError, TypeError):
                data['attributes'] = {}

        return data
