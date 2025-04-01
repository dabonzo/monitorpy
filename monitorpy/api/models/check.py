"""
Check model for the MonitorPy API.

This module defines the Check model for storing check configurations.
"""

import json
import uuid
from datetime import datetime

from monitorpy.api.extensions import db


class Check(db.Model):
    """
    Model representing a configured monitoring check.
    
    This stores the configuration for a monitoring check that can be
    executed on demand or on a schedule.
    """
    
    __tablename__ = 'checks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    plugin_type = db.Column(db.String(50), nullable=False)
    config = db.Column(db.Text, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    schedule = db.Column(db.String(50), nullable=True)
    last_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    results = db.relationship('Result', backref='check', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, plugin_type, config, enabled=True, schedule=None):
        """
        Initialize a new Check.
        
        Args:
            name: Human-readable name for the check
            plugin_type: Type of plugin to use for this check
            config: Configuration dictionary for the plugin
            enabled: Whether the check is enabled
            schedule: Schedule expression (e.g., "every 5 minutes")
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.plugin_type = plugin_type
        
        # Store config as JSON string
        if isinstance(config, dict):
            self.config = json.dumps(config)
        else:
            self.config = config
            
        self.enabled = enabled
        self.schedule = schedule
    
    def get_config(self):
        """
        Get the configuration as a dictionary.
        
        Returns:
            dict: Check configuration
        """
        return json.loads(self.config)
    
    def set_config(self, config):
        """
        Set the configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
        """
        self.config = json.dumps(config)
    
    def to_dict(self):
        """
        Convert the check to a dictionary.
        
        Returns:
            dict: Check data
        """
        return {
            'id': self.id,
            'name': self.name,
            'plugin_type': self.plugin_type,
            'config': self.get_config(),
            'enabled': self.enabled,
            'schedule': self.schedule,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        """Get string representation."""
        return f"<Check {self.name} ({self.plugin_type})>"