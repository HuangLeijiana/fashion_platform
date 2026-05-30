import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, redirect
from sqlalchemy import inspect, text


def create_app(config_class=None):
    """创建并配置 Flask 应用。"""
    if config_class is None:
        from config.default import DevelopmentConfig
        config_class = DevelopmentConfig

    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
    app = Flask(__name__, template_folder=template_dir, static_folder='../static')
    app.config.from_object(config_class)

    # Swagger/OpenAPI 配置
    app.config['SWAGGER'] = {
        'title': '云裳衣裳 API',
        'uiversion': 3,
        'openapi': '3.0.3',
        'specs_route': '/api/docs/',
    }

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .extensions import db, login_manager, mail
    from . import models  # noqa: F401
    from flasgger import Swagger

    db.init_app(app)
    mail.init_app(app)

    # 初始化 Swagger/OpenAPI 文档
    swagger_config = {
        'headers': [],
        'specs': [{
            'endpoint': 'apispec',
            'route': '/apispec.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }],
        'static_url_path': '/flasgger_static',
        'swagger_ui': True,
        'specs_route': '/api/docs/',
    }
    Swagger(app, template_file='../docs/openapi.yml', config=swagger_config)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return db.session.get(User, user_id)

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        from flask import request, url_for
        if request.path.startswith('/api/') or request.path.startswith('/recommendation/'):
            return jsonify({
                'success': False,
                'error': '需要登录',
                'redirect': url_for('auth.login')
            }), 401
        return redirect(url_for('auth.login', next=request.full_path))

    from .main.views import main_bp
    from .auth.routes import auth_bp
    from .wardrobe.views import wardrobe_bp
    from .search.views import search_bp
    from .recommendation.views import recommendation_bp
    from .style_analysis.views import style_analysis_bp
    from .fashion_advisor.views import fashion_advisor_bp
    from .analytics.views import analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(wardrobe_bp, url_prefix='/wardrobe')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(style_analysis_bp, url_prefix='/style-analysis')
    app.register_blueprint(fashion_advisor_bp)
    app.register_blueprint(analytics_bp)

    _setup_logging(app)

    with app.app_context():
        try:
            db.create_all()
            app.logger.info('数据库表创建成功')
            _ensure_schema_compat(db)
            create_default_admin(app)
        except Exception as exc:
            app.logger.error('数据库初始化失败: %s', exc)

    return app


def _ensure_schema_compat(db):
    """补齐旧数据库中缺失的新增字段。

    db.create_all() 只会创建不存在的表，不会修改已存在的表。旧库缺字段时，
    ORM 查询会把模型里的列一起 SELECT 出来，从而触发 Unknown column。
    """
    engine = db.engine
    inspector = inspect(engine)
    if 'clothing_items' not in inspector.get_table_names():
        return

    existing_columns = {
        column['name']
        for column in inspector.get_columns('clothing_items')
    }
    if 'updated_at' in existing_columns:
        return

    dialect = engine.dialect.name
    if dialect == 'mysql':
        ddl = (
            'ALTER TABLE clothing_items '
            'ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP '
            'ON UPDATE CURRENT_TIMESTAMP'
        )
    else:
        ddl = (
            'ALTER TABLE clothing_items '
            'ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        )

    db.session.execute(text(ddl))
    db.session.commit()


def _setup_logging(app):
    """配置应用日志。"""
    if not app.config.get('FEATURE_ANALYTICS_EVENTS', True):
        return

    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(logs_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(logs_dir, 'analytics.log'),
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    app.logger.addHandler(handler)


def create_default_admin(app):
    """创建默认管理员账户。"""
    from .models import User, db

    admin_user = User.query.filter_by(username='admin').first()
    if admin_user is None:
        admin_user = User(
            email='admin@example.com',
            username='admin',
            profile={'name': '系统管理员', 'gender': '男'}
        )
        db.session.add(admin_user)

    admin_user.set_password('admin123')
    admin_user.is_admin = True
    db.session.commit()
    app.logger.info('默认管理员账户已准备完成')
