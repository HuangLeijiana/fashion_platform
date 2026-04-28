import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-me')
    DEBUG = False
    TESTING = False

    # MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'fashion_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@yunxiangyishang.com')

    # Feature flags
    FEATURE_WARDROBE_RECOMMENDATION = True
    FEATURE_ANALYTICS_EVENTS = True
    FEATURE_SEARCH_WARDROBE_API = True
    FEATURE_ADVISOR_DIAGNOSIS = True
    FEATURE_WEATHER_SERVICE = True

    # Weather
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_USE_SIGNER = True


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
