# Writing Plugins

One of the key features of MonitorPy is its extensible plugin architecture. This guide explains how to write your own monitoring plugins to extend the system's capabilities.

## Plugin Architecture

MonitorPy plugins are Python classes that inherit from the `MonitorPlugin` base class and implement specific methods. Each plugin is registered with a unique name that users can reference when running checks.

## Creating a Basic Plugin

Here's a step-by-step guide to creating a new monitoring plugin:

### 1. Create a New Python Module

Create a new Python file in the `monitorpy/monitorpy/plugins` directory. For example, `dns_plugin.py`.

### 2. Import Required Components

```python
from typing import Dict, Any, List
import time
import dns.resolver  # Example: using dnspython library

from monitorpy.core import MonitorPlugin, CheckResult, register_plugin
from monitorpy.utils import get_logger

# Configure logging
logger = get_logger("plugins.dns")
```

### 3. Define Your Plugin Class

Create a class that inherits from `MonitorPlugin` and implements the required methods:

```python
@register_plugin("dns_record")
class DNSRecordPlugin(MonitorPlugin):
    """
    Plugin for checking DNS records.
    
    Verifies that a domain has the expected DNS records.
    """
    
    @classmethod
    def get_required_config(cls) -> List[str]:
        """Get required configuration parameters."""
        return ["domain", "record_type"]
    
    @classmethod
    def get_optional_config(cls) -> List[str]:
        """Get optional configuration parameters."""
        return ["expected_value", "nameserver", "timeout"]
    
    def validate_config(self) -> bool:
        """Validate that required configuration parameters are present and valid."""
        # Check that all required keys are present
        if not all(key in self.config for key in self.get_required_config()):
            return False
        
        # Validate record type
        record_type = self.config.get("record_type", "").upper()
        valid_types = ["A", "AAAA", "MX", "CNAME", "TXT", "NS", "SOA", "SRV"]
        if record_type not in valid_types:
            return False
        
        return True
    
    def run_check(self) -> CheckResult:
        """Run the DNS record check."""
        domain = self.config["domain"]
        record_type = self.config["record_type"].upper()
        expected_value = self.config.get("expected_value")
        nameserver = self.config.get("nameserver")
        timeout = self.config.get("timeout", 30)
        
        try:
            logger.debug(f"Checking DNS record {record_type} for {domain}")
            start_time = time.time()
            
            # Create a resolver
            resolver = dns.resolver.Resolver()
            if nameserver:
                resolver.nameservers = [nameserver]
            resolver.timeout = timeout
            
            # Query the DNS record
            answers = resolver.resolve(domain, record_type)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Check the results
            if not answers:
                return CheckResult(
                    CheckResult.STATUS_ERROR,
                    f"No {record_type} records found for {domain}",
                    response_time
                )
            
            # Convert answers to strings for comparison and display
            answer_values = [str(rdata) for rdata in answers]
            
            # Check against expected value if provided
            if expected_value and expected_value not in answer_values:
                return CheckResult(
                    CheckResult.STATUS_ERROR,
                    f"Expected value '{expected_value}' not found in {record_type} records for {domain}",
                    response_time,
                    {"records": answer_values}
                )
            
            # Return success result
            return CheckResult(
                CheckResult.STATUS_SUCCESS,
                f"DNS {record_type} record check successful for {domain}",
                response_time,
                {"records": answer_values}
            )
            
        except dns.resolver.NXDOMAIN:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Domain {domain} does not exist",
                time.time() - start_time
            )
        except dns.resolver.NoAnswer:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"No {record_type} records found for {domain}",
                time.time() - start_time
            )
        except dns.resolver.Timeout:
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Timeout resolving {record_type} records for {domain}",
                timeout
            )
        except Exception as e:
            logger.exception(f"Error checking DNS records for {domain}")
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Error checking DNS records: {str(e)}",
                time.time() - start_time,
                {"error": str(e), "error_type": type(e).__name__}
            )
```

### 4. Register the Plugin

Import your plugin in the `monitorpy/monitorpy/plugins/__init__.py` file:

```python
from monitorpy.plugins.website import WebsiteStatusPlugin
from monitorpy.plugins.ssl_certificate import SSLCertificatePlugin
from monitorpy.plugins.dns_plugin import DNSRecordPlugin  # Add your plugin here

__all__ = [
    'WebsiteStatusPlugin',
    'SSLCertificatePlugin',
    'DNSRecordPlugin',  # Add your plugin here
]
```

## Required Methods

When creating a plugin, you must implement the following methods:

### `get_required_config()`

This class method returns a list of configuration keys that are required for the plugin to function. The plugin will fail validation if any of these keys are missing from the configuration.

```python
@classmethod
def get_required_config(cls) -> List[str]:
    return ["key1", "key2"]
```

### `get_optional_config()`

This class method returns a list of configuration keys that are optional for the plugin. These are used for documentation purposes.

```python
@classmethod
def get_optional_config(cls) -> List[str]:
    return ["optional_key1", "optional_key2"]
```

### `validate_config()`

This method checks if the provided configuration is valid. It should return `True` if the configuration is valid, and `False` otherwise.

```python
def validate_config(self) -> bool:
    # Check for required keys
    if not all(key in self.config for key in self.get_required_config()):
        return False
    
    # Additional validation checks
    if some_condition:
        return False
    
    return True
```

### `run_check()`

This is the main method that performs the monitoring check. It should return a `CheckResult` object.

```python
def run_check(self) -> CheckResult:
    # Perform the check
    # ...
    
    # Return result
    return CheckResult(
        status=CheckResult.STATUS_SUCCESS,  # or WARNING or ERROR
        message="Human-readable message",
        response_time=execution_time,
        raw_data={"additional": "data"}
    )
```

## Best Practices

When developing plugins, follow these best practices:

1. **Proper Error Handling**: Catch all exceptions and return appropriate error messages.

2. **Detailed Logging**: Use the logger to record important events and errors.

3. **Accurate Timing**: Measure and report the response time for checks.

4. **Descriptive Messages**: Provide clear, informative messages in the CheckResult.

5. **Thorough Validation**: Validate the configuration thoroughly to prevent runtime errors.

6. **Comprehensive Documentation**: Document the plugin's purpose, requirements, and behavior.

7. **Stateless Design**: Plugins should be stateless and not rely on external state between runs.

## Testing Your Plugin

Create a test file in the `tests` directory to verify your plugin works correctly:

```python
import unittest
from monitorpy.core import run_check

class TestDNSPlugin(unittest.TestCase):
    def test_basic_dns_check(self):
        config = {
            "domain": "example.com",
            "record_type": "A"
        }
        
        result = run_check("dns_record", config)
        self.assertTrue(result.is_success())
    
    def test_invalid_config(self):
        # Missing required config
        config = {
            "domain": "example.com"
        }
        
        result = run_check("dns_record", config)
        self.assertTrue(result.is_error())

if __name__ == '__main__':
    unittest.main()
```

## Adding CLI Support

To make your plugin available through the command-line interface, update the `cli.py` file to add a subparser for your plugin. This will allow users to run your plugin from the command line.

## Documentation

Don't forget to document your plugin by adding information to the appropriate documentation files, such as updating the examples and configuration documents.
