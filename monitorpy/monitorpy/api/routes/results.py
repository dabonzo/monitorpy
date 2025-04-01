"""
Result endpoints for the MonitorPy API.

This module defines API endpoints for result operations.
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta

from monitorpy.api.extensions import db
from monitorpy.api.models import Result

bp = Blueprint('results', __name__)


@bp.route('', methods=['GET'])
def get_results():
    """
    Get a list of check results.
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: from config)
        check_id: Filter by check ID
        status: Filter by status (success, warning, error)
        from_date: Filter by execution date (ISO format)
        to_date: Filter by execution date (ISO format)
        
    Returns:
        JSON response with check results
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    
    # Limit per_page to prevent excessive queries
    per_page = min(per_page, current_app.config['MAX_PAGE_SIZE'])
    
    # Create base query
    query = Result.query
    
    # Apply filters
    if 'check_id' in request.args:
        query = query.filter(Result.check_id == request.args.get('check_id'))
    
    if 'status' in request.args:
        query = query.filter(Result.status == request.args.get('status'))
    
    # Date filtering
    if 'from_date' in request.args:
        try:
            from_date = datetime.fromisoformat(request.args.get('from_date'))
            query = query.filter(Result.executed_at >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    if 'to_date' in request.args:
        try:
            to_date = datetime.fromisoformat(request.args.get('to_date'))
            query = query.filter(Result.executed_at <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    # Paginate results
    pagination = query.order_by(Result.executed_at.desc()).paginate(page=page, per_page=per_page)
    
    # Format response
    results = [result.to_dict() for result in pagination.items]
    
    return jsonify({
        'results': results,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/<string:result_id>', methods=['GET'])
def get_result(result_id):
    """
    Get a specific check result.
    
    Args:
        result_id: ID of the result
        
    Returns:
        JSON response with check result
    """
    result = Result.query.get(result_id)
    
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify(result.to_dict())


@bp.route('/check/<string:check_id>', methods=['GET'])
def get_check_results(check_id):
    """
    Get results for a specific check.
    
    Args:
        check_id: ID of the check
        
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: from config)
        status: Filter by status (success, warning, error)
        from_date: Filter by execution date (ISO format)
        to_date: Filter by execution date (ISO format)
        
    Returns:
        JSON response with check results
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    
    # Limit per_page to prevent excessive queries
    per_page = min(per_page, current_app.config['MAX_PAGE_SIZE'])
    
    # Create base query
    query = Result.query.filter(Result.check_id == check_id)
    
    # Apply filters
    if 'status' in request.args:
        query = query.filter(Result.status == request.args.get('status'))
    
    # Date filtering
    if 'from_date' in request.args:
        try:
            from_date = datetime.fromisoformat(request.args.get('from_date'))
            query = query.filter(Result.executed_at >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    if 'to_date' in request.args:
        try:
            to_date = datetime.fromisoformat(request.args.get('to_date'))
            query = query.filter(Result.executed_at <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    # Paginate results
    pagination = query.order_by(Result.executed_at.desc()).paginate(page=page, per_page=per_page)
    
    # Format response
    results = [result.to_dict() for result in pagination.items]
    
    return jsonify({
        'check_id': check_id,
        'results': results,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@bp.route('/summary', methods=['GET'])
def get_results_summary():
    """
    Get a summary of check results.
    
    Query parameters:
        period: Time period for the summary (day, week, month)
        
    Returns:
        JSON response with result summary statistics
    """
    # Get time period
    period = request.args.get('period', 'day')
    
    # Calculate date range
    now = datetime.utcnow()
    
    if period == 'week':
        from_date = now - timedelta(days=7)
    elif period == 'month':
        from_date = now - timedelta(days=30)
    else:  # day or invalid input
        from_date = now - timedelta(days=1)
    
    # Get counts by status
    success_count = Result.query.filter(
        Result.status == 'success',
        Result.executed_at >= from_date
    ).count()
    
    warning_count = Result.query.filter(
        Result.status == 'warning',
        Result.executed_at >= from_date
    ).count()
    
    error_count = Result.query.filter(
        Result.status == 'error',
        Result.executed_at >= from_date
    ).count()
    
    total_count = success_count + warning_count + error_count
    
    # Calculate percentages
    success_percent = (success_count / total_count * 100) if total_count > 0 else 0
    warning_percent = (warning_count / total_count * 100) if total_count > 0 else 0
    error_percent = (error_count / total_count * 100) if total_count > 0 else 0
    
    return jsonify({
        'period': period,
        'from_date': from_date.isoformat(),
        'to_date': now.isoformat(),
        'total_checks': total_count,
        'statuses': {
            'success': {
                'count': success_count,
                'percent': round(success_percent, 2)
            },
            'warning': {
                'count': warning_count,
                'percent': round(warning_percent, 2)
            },
            'error': {
                'count': error_count,
                'percent': round(error_percent, 2)
            }
        }
    })