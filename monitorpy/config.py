"""
Central configuration module for MonitorPy.

This module loads and provides configuration settings for all components
of MonitorPy from a central configuration file.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional

# Set up module logger
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manager for loading and accessing configuration settings.
    
    This class handles loading configuration from files and environment
    variables, and provides access to settings for different components.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "general": {
            "log_level": "INFO",
            "log_file": None,
            "data_dir": "~/.monitorpy"
        },
        "api": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            "secret_key": "dev-key-please-change-in-production",
            "jwt_secret_key": "jwt-dev-key-please-change",
            "auth_required": False,
            "result_retention_days": 30
        },
        "database": {
            "type": "sqlite",  # sqlite, postgresql, mysql
            "path": "~/.monitorpy/monitorpy.db",  # For sqlite
            "host": "localhost",  # For postgresql, mysql
            "port": None,  # For postgresql, mysql
            "name": "monitorpy",  # For postgresql, mysql
            "user": "monitorpy",  # For postgresql, mysql
            "password": None,  # For postgresql, mysql
            "ssl": False  # For postgresql, mysql
        },
        "plugins": {
            "website": {
                "default_timeout": 30,
                "user_agent": "MonitorPy/1.0"
            },
            "ssl": {
                "default_timeout": 30,
                "warning_days": 30,
                "critical_days": 14
            },
            "mail": {
                "default_timeout": 30
            },
            "dns": {
                "default_timeout": 30
            }
        }
    }
    
    def __init__(self):
        """Initialize with default configuration."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = None
        
    def load_config(self, config_file: Optional[str] = None) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file. If not specified,
                         looks for config in standard locations.
        """
        # Look for config file in standard locations if not specified
        if not config_file:
            potential_locations = [
                # Current directory
                "./monitorpy.yml",
                "./monitorpy.yaml",
                "./monitorpy.json",
                # User's home directory
                os.path.expanduser("~/.monitorpy/config.yml"),
                os.path.expanduser("~/.monitorpy/config.yaml"),
                os.path.expanduser("~/.monitorpy/config.json"),
                # System config
                "/etc/monitorpy/config.yml",
                "/etc/monitorpy/config.yaml",
                "/etc/monitorpy/config.json"
            ]
            
            # Check environment variable
            if "MONITORPY_CONFIG" in os.environ:
                potential_locations.insert(0, os.environ["MONITORPY_CONFIG"])
                
            # Find first existing config file
            for loc in potential_locations:
                if os.path.isfile(loc):
                    config_file = loc
                    break
        
        # Load configuration if a file was found
        if config_file and os.path.isfile(config_file):
            try:
                self.config_file = config_file
                
                # Load based on file extension
                if config_file.endswith((".yml", ".yaml")):
                    with open(config_file, "r") as f:
                        file_config = yaml.safe_load(f)
                elif config_file.endswith(".json"):
                    with open(config_file, "r") as f:
                        file_config = json.load(f)
                else:
                    logger.warning(f"Unknown config file format: {config_file}")
                    return
                
                # Update config with loaded values
                self._update_nested_dict(self.config, file_config)
                logger.info(f"Loaded configuration from {config_file}")
                
            except Exception as e:
                logger.error(f"Error loading config file {config_file}: {str(e)}")
                
        else:
            logger.info("No configuration file found, using defaults")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """
        Update a nested dictionary with values from another dictionary.
        
        Args:
            d: Dictionary to update
            u: Dictionary with new values
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def get_database_url(self) -> str:
        """
        Get a database URL for SQLAlchemy.
        
        Returns:
            Database URL string
        """
        db_config = self.config["database"]
        db_type = db_config["type"]
        
        # Override with environment variable if set
        if "DATABASE_URL" in os.environ:
            return os.environ["DATABASE_URL"]
        
        if db_type == "sqlite":
            path = os.path.expanduser(db_config["path"])
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return f"sqlite:///{path}"
        
        elif db_type == "postgresql":
            password = db_config["password"] or ""
            port = db_config["port"] or 5432
            return f"postgresql://{db_config['user']}:{password}@{db_config['host']}:{port}/{db_config['name']}"
        
        elif db_type == "mysql":
            password = db_config["password"] or ""
            port = db_config["port"] or 3306
            return f"mysql+pymysql://{db_config['user']}:{password}@{db_config['host']}:{port}/{db_config['name']}"
        
        else:
            logger.warning(f"Unknown database type: {db_type}, defaulting to SQLite")
            return "sqlite:///monitorpy.db"
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Configuration section
            
        Returns:
            Section dictionary or empty dict if not found
        """
        return self.config.get(section, {})
    
    def save_sample_config(self, file_path: str, format: str = "yaml") -> None:
        """
        Save a sample configuration file.
        
        Args:
            file_path: Path where to save the file
            format: Format of the file (yaml or json)
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if format.lower() == "json":
                with open(file_path, "w") as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=2)
            else:
                with open(file_path, "w") as f:
                    yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False)
                    
            logger.info(f"Saved sample configuration to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving sample config: {str(e)}")


# Create a singleton instance
config = ConfigManager()

# Load configuration on import
config.load_config()


def get_config(section: str, key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    return config.get(section, key, default)


def get_section(section: str) -> Dict[str, Any]:
    """
    Get an entire configuration section.
    
    Args:
        section: Configuration section
        
    Returns:
        Section dictionary or empty dict if not found
    """
    return config.get_section(section)


def get_database_url() -> str:
    """
    Get a database URL for SQLAlchemy.
    
    Returns:
        Database URL string
    """
    return config.get_database_url()


def load_config(config_file: str) -> None:
    """
    Load configuration from a file.
    
    Args:
        config_file: Path to the configuration file
    """
    config.load_config(config_file)


def save_sample_config(file_path: str, format: str = "yaml") -> None:
    """
    Save a sample configuration file.
    
    Args:
        file_path: Path where to save the file
        format: Format of the file (yaml or json)
    """
    config.save_sample_config(file_path, format)