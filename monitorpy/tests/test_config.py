"""
Tests for the configuration system.

These tests verify that the configuration system loads and processes
configuration values correctly.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import yaml
import json

from monitorpy.config import ConfigManager, get_config, get_section, get_database_url


class TestConfigManager(unittest.TestCase):
    """Test suite for the ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        
        # Create a temporary YAML config file
        self.yaml_config = {
            "general": {
                "log_level": "DEBUG",
                "log_file": "/tmp/test.log"
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8080
            },
            "database": {
                "type": "sqlite",
                "path": "/tmp/test.db"
            }
        }
        
        self.yaml_file = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        with open(self.yaml_file.name, "w") as f:
            yaml.dump(self.yaml_config, f)
            
        # Create a temporary JSON config file
        self.json_config = {
            "general": {
                "log_level": "ERROR",
                "log_file": "/tmp/test2.log"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 9090
            }
        }
        
        self.json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        with open(self.json_file.name, "w") as f:
            json.dump(self.json_config, f)
    
    def tearDown(self):
        """Clean up after tests."""
        os.unlink(self.yaml_file.name)
        os.unlink(self.json_file.name)
    
    def test_default_config(self):
        """Test that default configuration values are set."""
        # Create a new config manager to ensure defaults
        config = ConfigManager()
        
        # Check some default values
        self.assertEqual(config.get("general", "log_level"), "INFO")
        self.assertEqual(config.get("api", "port"), 5000)
        self.assertEqual(config.get("database", "type"), "sqlite")
    
    def test_load_yaml_config(self):
        """Test loading configuration from a YAML file."""
        self.config_manager.load_config(self.yaml_file.name)
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.get("general", "log_level"), "DEBUG")
        self.assertEqual(self.config_manager.get("general", "log_file"), "/tmp/test.log")
        self.assertEqual(self.config_manager.get("api", "host"), "127.0.0.1")
        self.assertEqual(self.config_manager.get("api", "port"), 8080)
        
        # Check that defaults are still used for unspecified values
        self.assertEqual(self.config_manager.get("api", "debug"), False)
    
    def test_load_json_config(self):
        """Test loading configuration from a JSON file."""
        self.config_manager.load_config(self.json_file.name)
        
        # Check that values were loaded correctly
        self.assertEqual(self.config_manager.get("general", "log_level"), "ERROR")
        self.assertEqual(self.config_manager.get("general", "log_file"), "/tmp/test2.log")
        self.assertEqual(self.config_manager.get("api", "host"), "0.0.0.0")
        self.assertEqual(self.config_manager.get("api", "port"), 9090)
    
    def test_get_with_default(self):
        """Test getting a value with a default fallback."""
        # Value exists in config
        self.config_manager.config["test"] = {"key": "value"}
        self.assertEqual(self.config_manager.get("test", "key"), "value")
        
        # Value doesn't exist, use default
        self.assertEqual(self.config_manager.get("test", "nonexistent", "default"), "default")
        
        # Section doesn't exist, use default
        self.assertEqual(self.config_manager.get("nonexistent", "key", "default"), "default")
    
    def test_get_section(self):
        """Test getting an entire configuration section."""
        self.config_manager.config["test"] = {"key1": "value1", "key2": "value2"}
        
        section = self.config_manager.get_section("test")
        self.assertEqual(section, {"key1": "value1", "key2": "value2"})
        
        # Nonexistent section
        self.assertEqual(self.config_manager.get_section("nonexistent"), {})
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/db"})
    def test_database_url_env_var_override(self):
        """Test that environment variable overrides database URL."""
        url = self.config_manager.get_database_url()
        self.assertEqual(url, "postgresql://user:pass@localhost/db")
    
    def test_database_url_sqlite(self):
        """Test SQLite database URL generation."""
        self.config_manager.config["database"] = {
            "type": "sqlite",
            "path": "/tmp/test.db"
        }
        
        url = self.config_manager.get_database_url()
        self.assertEqual(url, "sqlite:////tmp/test.db")
    
    def test_database_url_postgresql(self):
        """Test PostgreSQL database URL generation."""
        self.config_manager.config["database"] = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "name": "testdb",
            "user": "testuser",
            "password": "testpass"
        }
        
        url = self.config_manager.get_database_url()
        self.assertEqual(url, "postgresql://testuser:testpass@localhost:5432/testdb")
    
    def test_database_url_mysql(self):
        """Test MySQL database URL generation."""
        self.config_manager.config["database"] = {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "name": "testdb",
            "user": "testuser",
            "password": "testpass"
        }
        
        url = self.config_manager.get_database_url()
        self.assertEqual(url, "mysql+pymysql://testuser:testpass@localhost:3306/testdb")
    
    def test_update_nested_dict(self):
        """Test updating a nested dictionary."""
        base = {
            "level1": {
                "level2": {
                    "key": "original"
                },
                "key": "original"
            }
        }
        
        update = {
            "level1": {
                "level2": {
                    "key": "updated",
                    "new_key": "new_value"
                }
            },
            "new_level1": {
                "key": "new_value"
            }
        }
        
        self.config_manager._update_nested_dict(base, update)
        
        # Check that values were updated correctly
        self.assertEqual(base["level1"]["level2"]["key"], "updated")
        self.assertEqual(base["level1"]["level2"]["new_key"], "new_value")
        self.assertEqual(base["level1"]["key"], "original")  # Unchanged
        self.assertEqual(base["new_level1"]["key"], "new_value")
    
    def test_save_sample_config(self):
        """Test saving a sample configuration file."""
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create a fresh ConfigManager with default values
            clean_manager = ConfigManager()
            
            # Save a sample config from the clean manager
            clean_manager.save_sample_config(temp_path, "yaml")
            
            # Check that the file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Load the file and check that it contains default values
            with open(temp_path, "r") as f:
                sample_config = yaml.safe_load(f)
            
            # Check against the DEFAULT_CONFIG, not the instance config
            self.assertEqual(sample_config["general"]["log_level"], 
                             ConfigManager.DEFAULT_CONFIG["general"]["log_level"])
            self.assertEqual(sample_config["api"]["port"], 
                             ConfigManager.DEFAULT_CONFIG["api"]["port"])
            self.assertEqual(sample_config["database"]["type"], 
                             ConfigManager.DEFAULT_CONFIG["database"]["type"])
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestConfigFunctions(unittest.TestCase):
    """Test suite for the configuration module functions."""
    
    def test_get_config(self):
        """Test the get_config function."""
        # This function just delegates to the global config instance
        # so we'll just do a basic test
        value = get_config("general", "log_level", "DEBUG")
        self.assertIsNotNone(value)
    
    def test_get_section(self):
        """Test the get_section function."""
        # This function just delegates to the global config instance
        section = get_section("general")
        self.assertIsInstance(section, dict)
    
    def test_get_database_url(self):
        """Test the get_database_url function."""
        # This function just delegates to the global config instance
        url = get_database_url()
        self.assertIsNotNone(url)


if __name__ == "__main__":
    unittest.main()