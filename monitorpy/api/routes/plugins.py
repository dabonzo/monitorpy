"""
Plugin endpoints for the MonitorPy API.

This module defines API endpoints for plugin management.
"""

from flask import Blueprint, jsonify, request, current_app
from monitorpy.core.registry import registry

bp = Blueprint('plugins', __name__)


@bp.route('', methods=['GET'])
def get_plugins():
    """
    Get a list of all available plugins.
    
    Returns:
        JSON response with plugin information
    """
    plugins = registry.get_all_plugins()
    
    # Convert to list format for API
    plugin_list = []
    for name, info in plugins.items():
        plugin_list.append({
            'name': name,
            'description': info['description'],
            'required_config': info['required_config'],
            'optional_config': info['optional_config']
        })
    
    return jsonify({
        'plugins': plugin_list,
        'count': len(plugin_list)
    })


@bp.route('/<string:plugin_name>', methods=['GET'])
def get_plugin_info(plugin_name):
    """
    Get information about a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        JSON response with plugin information
    """
    plugins = registry.get_all_plugins()
    
    if plugin_name not in plugins:
        return jsonify({
            'error': 'Plugin not found',
            'available_plugins': list(plugins.keys())
        }), 404
    
    plugin_info = plugins[plugin_name]
    
    return jsonify({
        'name': plugin_name,
        'description': plugin_info['description'],
        'required_config': plugin_info['required_config'],
        'optional_config': plugin_info['optional_config']
    })