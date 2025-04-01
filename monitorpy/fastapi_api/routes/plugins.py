"""
Plugin endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for plugin management.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from monitorpy.core.registry import registry
from monitorpy.fastapi_api.deps import get_current_user

router = APIRouter()


@router.get("")
async def get_plugins(
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a list of all available plugins.
    
    Returns information about all available monitoring plugins.
    """
    plugins = registry.get_all_plugins()
    
    # Convert to list format for API
    plugin_list = []
    for name, info in plugins.items():
        plugin_list.append({
            "name": name,
            "description": info["description"],
            "required_config": info["required_config"],
            "optional_config": info["optional_config"]
        })
    
    return {
        "plugins": plugin_list,
        "count": len(plugin_list)
    }


@router.get("/{plugin_name}")
async def get_plugin_info(
    plugin_name: str,
    current_user: Dict = Depends(get_current_user),
):
    """
    Get information about a specific plugin.
    
    Returns detailed information about a specific plugin,
    including configuration requirements.
    """
    plugins = registry.get_all_plugins()
    
    if plugin_name not in plugins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Plugin not found",
                "available_plugins": list(plugins.keys())
            }
        )
    
    plugin_info = plugins[plugin_name]
    
    return {
        "name": plugin_name,
        "description": plugin_info["description"],
        "required_config": plugin_info["required_config"],
        "optional_config": plugin_info["optional_config"]
    }