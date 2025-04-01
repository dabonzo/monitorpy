"""
Configuration for the MonitorPy API.

This module provides configuration classes for the Flask application.
"""

import os
from datetime import timedelta
from monitorpy.config import get_config, get_database_url


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or get_config('api', 'secret_key')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or get_config('api', 'jwt_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    API_TITLE = 'MonitorPy API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Result storage
    RESULT_RETENTION_DAYS = get_config('api', 'result_retention_days', 30)
    
    # Authentication (disabled by default for development)
    AUTH_REQUIRED = os.environ.get('AUTH_REQUIRED', str(get_config('api', 'auth_required', False))).lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    
    # In production, these values must be set via environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Enable authentication by default in production
    AUTH_REQUIRED = os.environ.get('AUTH_REQUIRED', 'True').lower() == 'true'


# Map environment names to config classes
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


# Get config based on environment
def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name.get(env, DevelopmentConfig)