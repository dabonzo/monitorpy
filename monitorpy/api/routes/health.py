"""
Health check endpoints for the MonitorPy API.

This module defines API endpoints for health checking.
"""

from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)


@bp.route('', methods=['GET'])
def health_check():
    """
    Get API health status.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'version': '1.0.0'
    })