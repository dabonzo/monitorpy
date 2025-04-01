"""
Authentication routes for the MonitorPy API.

This module provides endpoints for user authentication.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from monitorpy.api.extensions import db, jwt
from monitorpy.api.models.user import User
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password"
        }
        
    Returns:
        JSON with access token on success, error message on failure
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        logger.warning(f"Failed login attempt for user {email}")
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    logger.info(f"User {email} logged in successfully")
    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200