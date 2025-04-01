"""
Flask application for MonitorPy API.

This module provides a Flask application that exposes MonitorPy functionality
through a REST API.
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from monitorpy.api.extensions import db
from monitorpy.api.config import Config
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)


def create_app(config_class=Config):
    """
    Create and configure the Flask application.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    Migrate(app, db)
    
    # Register blueprints
    from monitorpy.api.routes.checks import bp as checks_bp
    from monitorpy.api.routes.results import bp as results_bp
    from monitorpy.api.routes.plugins import bp as plugins_bp
    from monitorpy.api.routes.health import bp as health_bp
    
    app.register_blueprint(checks_bp, url_prefix='/api/v1/checks')
    app.register_blueprint(results_bp, url_prefix='/api/v1/results')
    app.register_blueprint(plugins_bp, url_prefix='/api/v1/plugins')
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    
    # Create database tables if needed
    with app.app_context():
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
            # SQLite database - create directory if needed
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if db_path:  # Skip for in-memory database
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        db.create_all()
    
    @app.route('/')
    def index():
        return {
            "name": "MonitorPy API",
            "version": "1.0.0",
            "endpoints": [
                "/api/v1/health",
                "/api/v1/plugins",
                "/api/v1/checks",
                "/api/v1/results"
            ]
        }
    
    return app