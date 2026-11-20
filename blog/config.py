import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file upload

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "1", "t"]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ["true", "1", "t"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


class DevConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SOCIALBLOG_ADMIN = os.environ.get("SOCIALBLOG_ADMIN", "admin@example.com")
    FLASKY_FOLLOWERS_PER_PAGE = 4


class TestConfig(Config):
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False


class ProdConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY")

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///prod.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    DEBUG = False
    SQLALCHEMY_ECHO = False

    _use_https = os.environ.get("HTTPS_ENABLED", "false").lower() in ["true", "1", "t"]
    SESSION_COOKIE_SECURE = _use_https
    REMEMBER_COOKIE_SECURE = _use_https
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
