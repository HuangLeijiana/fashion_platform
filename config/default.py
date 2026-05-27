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
    WEATHER_API_BASE = os.environ.get('WEATHER_API_BASE', 'https://api.openweathermap.org/data/2.5/weather')

    # Advisor / LLM
    ADVISOR_LLM_PROVIDER = os.environ.get('ADVISOR_LLM_PROVIDER', 'auto')
    ADVISOR_LLM_MODEL = os.environ.get('ADVISOR_LLM_MODEL', os.environ.get('OLLAMA_MODEL', 'qwen2.5:3b'))
    ADVISOR_OLLAMA_HOST = os.environ.get('ADVISOR_OLLAMA_HOST', os.environ.get('OLLAMA_HOST', 'http://localhost:11434'))
    ADVISOR_OPENAI_API_KEY = os.environ.get('ADVISOR_OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
    ADVISOR_OPENAI_BASE_URL = os.environ.get('ADVISOR_OPENAI_BASE_URL', os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'))
    ADVISOR_VECTOR_TOP_K = int(os.environ.get('ADVISOR_VECTOR_TOP_K', 3))
    FEATURE_ADVISOR_RAG = os.environ.get('FEATURE_ADVISOR_RAG', 'true').lower() in ['true', 'on', '1']
    FEATURE_ADVISOR_AGENT = os.environ.get('FEATURE_ADVISOR_AGENT', 'true').lower() in ['true', 'on', '1']
    FEATURE_ADVISOR_LANGCHAIN = os.environ.get('FEATURE_ADVISOR_LANGCHAIN', 'false').lower() in ['true', 'on', '1']
    FEATURE_ADVISOR_LANGGRAPH = os.environ.get('FEATURE_ADVISOR_LANGGRAPH', 'false').lower() in ['true', 'on', '1']
    FEATURE_ASYNC_INDEXING = os.environ.get('FEATURE_ASYNC_INDEXING', 'false').lower() in ['true', 'on', '1']
    CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', 'chroma_data')
    SENTENCE_TRANSFORMERS_HOME = os.environ.get('SENTENCE_TRANSFORMERS_HOME', os.path.join('app', 'models', 'text2vec'))

    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_USE_SIGNER = True

    # Ollama LLM
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', 60))

    # Fashion Advisor Agent
    ADVISOR_MAX_TOKENS = int(os.environ.get('ADVISOR_MAX_TOKENS', 512))
    ADVISOR_TEMPERATURE = float(os.environ.get('ADVISOR_TEMPERATURE', 0.7))


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
