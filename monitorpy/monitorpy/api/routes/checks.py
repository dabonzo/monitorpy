"""
Check endpoints for the MonitorPy API.

This module defines API endpoints for check operations.
"""

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError

from monitorpy.api.extensions import db
from monitorpy.api.models import Check, Result
from monitorpy.core.registry import run_check as execute_check

bp = Blueprint('checks', __name__)


@bp.route('', methods=['GET'])
def get_checks():
    """
    Get a list of all configured checks.
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: from config)
        enabled: Filter by enabled status (true/false)
        plugin_type: Filter by plugin type
        
    Returns:
        JSON response with check configurations
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    
    # Limit per_page to prevent excessive queries
    per_page = min(per_page, current_app.config['MAX_PAGE_SIZE'])
    
    # Create base query
    query = Check.query
    
    # Apply filters
    if 'enabled' in request.args:
        enabled = request.args.get('enabled').lower() == 'true'
        query = query.filter(Check.enabled == enabled)
    
    if 'plugin_type' in request.args:
        query = query.filter(Check.plugin_type == request.args.get('plugin_type'))
    
    # Paginate results
    pagination = query.order_by(Check.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Format response
    checks = [check.to_dict() for check in pagination.items]
    
    return jsonify({
        'checks': checks,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/<string:check_id>', methods=['GET'])
def get_check(check_id):
    """
    Get a specific check configuration.
    
    Args:
        check_id: ID of the check
        
    Returns:
        JSON response with check configuration
    """
    check = Check.query.get(check_id)
    
    if not check:
        return jsonify({'error': 'Check not found'}), 404
    
    return jsonify(check.to_dict())


@bp.route('', methods=['POST'])
def create_check():
    """
    Create a new check configuration.
    
    Request body:
        name: Human-readable name for the check
        plugin_type: Type of plugin to use
        config: Configuration for the plugin
        enabled: Whether the check is enabled
        schedule: Schedule expression (optional)
        
    Returns:
        JSON response with created check
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'plugin_type', 'config']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create new check
    try:
        check = Check(
            name=data['name'],
            plugin_type=data['plugin_type'],
            config=data['config'],
            enabled=data.get('enabled', True),
            schedule=data.get('schedule')
        )
        
        db.session.add(check)
        db.session.commit()
        
        return jsonify(check.to_dict()), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@bp.route('/<string:check_id>', methods=['PUT'])
def update_check(check_id):
    """
    Update an existing check configuration.
    
    Args:
        check_id: ID of the check to update
        
    Request body:
        name: Human-readable name for the check
        plugin_type: Type of plugin to use
        config: Configuration for the plugin
        enabled: Whether the check is enabled
        schedule: Schedule expression
        
    Returns:
        JSON response with updated check
    """
    check = Check.query.get(check_id)
    
    if not check:
        return jsonify({'error': 'Check not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if 'name' in data:
            check.name = data['name']
        
        if 'plugin_type' in data:
            check.plugin_type = data['plugin_type']
        
        if 'config' in data:
            check.set_config(data['config'])
        
        if 'enabled' in data:
            check.enabled = data['enabled']
        
        if 'schedule' in data:
            check.schedule = data['schedule']
        
        db.session.commit()
        
        return jsonify(check.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@bp.route('/<string:check_id>', methods=['DELETE'])
def delete_check(check_id):
    """
    Delete a check configuration.
    
    Args:
        check_id: ID of the check to delete
        
    Returns:
        Empty response with 204 status
    """
    check = Check.query.get(check_id)
    
    if not check:
        return jsonify({'error': 'Check not found'}), 404
    
    try:
        db.session.delete(check)
        db.session.commit()
        
        return '', 204
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@bp.route('/<string:check_id>/run', methods=['POST'])
def run_check(check_id):
    """
    Run a check immediately and store the result.
    
    Args:
        check_id: ID of the check to run
        
    Returns:
        JSON response with check result
    """
    check = Check.query.get(check_id)
    
    if not check:
        return jsonify({'error': 'Check not found'}), 404
    
    try:
        # Run the check
        config = check.get_config()
        check_result = execute_check(check.plugin_type, config)
        
        # Store the result
        result = Result.from_check_result(check_id, check_result)
        
        db.session.add(result)
        check.last_run = result.executed_at
        db.session.commit()
        
        return jsonify(result.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error running check: {str(e)}'}), 500


@bp.route('/run', methods=['POST'])
def run_ad_hoc_check():
    """
    Run an ad-hoc check without storing configuration.
    
    Request body:
        plugin_type: Type of plugin to use
        config: Configuration for the plugin
        
    Returns:
        JSON response with check result
    """
    data = request.get_json()
    
    # Validate required fields
    if 'plugin_type' not in data:
        return jsonify({'error': 'Missing required field: plugin_type'}), 400
    
    if 'config' not in data:
        return jsonify({'error': 'Missing required field: config'}), 400
    
    try:
        # Run the check
        check_result = execute_check(data['plugin_type'], data['config'])
        
        # Return the result without storing
        return jsonify(check_result.to_dict())
    
    except Exception as e:
        return jsonify({'error': f'Error running check: {str(e)}'}), 500