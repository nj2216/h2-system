"""
Configuration file for H2 System (Health & Hostel Management System)
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///h2_system.db'
    # Some platforms still provide postgres://; SQLAlchemy expects postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        # SQLite is file-based; keep pooling minimal and increase lock wait time.
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'timeout': int(os.environ.get('SQLITE_TIMEOUT', 30))
            }
        }
    else:
        # Server databases (PostgreSQL/MySQL) benefit from explicit pooling.
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 15)),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800))
        }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False  # Set to False for development
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to False for development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
