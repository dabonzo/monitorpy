# Sample Plugin Examples

This page provides practical examples of using the sample monitoring plugins in various scenarios.

## Basic Usage Examples

### Simple Target Monitoring

Monitor a single target with default settings:

```yaml
checks:
  - type: sample_monitor
    name: basic_monitor
    target: example.com
    check_interval: 60
```

This configuration will check the target `example.com` every 60 seconds using default settings for timeout and thresholds.

### Multiple Targets with Custom Thresholds

```yaml
checks:
  - type: sample_monitor
    name: production_api
    target: api.production.example.com
    check_interval: 30
    timeout: 15
    warning_threshold: 3.0
    
  - type: sample_monitor
    name: staging_api
    target: api.staging.example.com
    check_interval: 120
    timeout: 30
    warning_threshold: 10.0  # Higher threshold for non-production
```

### Using Retry Logic

```yaml
checks:
  - type: sample_monitor
    name: flaky_service
    target: flaky-service.example.com
    check_interval: 60
    timeout: 20
    retry_count: 3  # Will retry up to 3 times before reporting failure
```

## API Monitoring Examples

### Basic API Endpoint Check

```yaml
checks:
  - type: custom_api_monitor
    name: status_api
    target: api.example.com
    check_interval: 300
    api_key: YOUR_API_KEY_HERE
    endpoint: /v1/status
```

### API Monitor with Custom Headers and Query Parameters

```yaml
checks:
  - type: custom_api_monitor
    name: detailed_api_check
    target: api.example.com
    check_interval: 300
    api_key: YOUR_API_KEY_HERE
    endpoint: /v1/resources
    headers:
      Accept: application/json
      X-Client-ID: monitoring-service
    query_params:
      detailed: true
      format: json
```

## Integration with Alerts

You can integrate sample checks with the MonitorPy alerting system:

```yaml
checks:
  - type: sample_monitor
    name: critical_service
    target: critical.example.com
    check_interval: 30
    timeout: 10
    warning_threshold: 2.0
    alerts:
      - type: email
        recipients: 
          - ops@example.com
          - oncall@example.com
      - type: slack
        channel: #monitoring-alerts
```

## Command Line Usage

To run a check from the command line:

```bash
monitorpy check sample_monitor --target example.com --check-interval 60
```

For a custom API monitor:

```bash
monitorpy check custom_api_monitor --target api.example.com --api-key YOUR_KEY --endpoint /status
```

## Development Examples

### Extending the Sample Plugin

You can extend the sample plugin for your own custom monitoring needs:

```python
from monitorpy.plugins.sample_template import SampleMonitorPlugin
from monitorpy.core.registry import register_plugin

@register_plugin("my_custom_monitor")
class MyCustomMonitor(SampleMonitorPlugin):
    """Custom monitoring plugin for specific needs."""
    
    @classmethod
    def get_required_config(cls):
        # Extend the parent's required config
        return super().get_required_config() + ["my_custom_param"]
    
    def _execute_check(self):
        # Access the parent configuration
        target = self.config["target"]
        
        # Access custom configuration
        custom_param = self.config["my_custom_param"]
        
        # Your custom implementation here
        # ...
        
        # Use the helper methods
        return self.success_result(
            f"Custom check successful for {target}",
            response_time=0.5,
            raw_data={"custom_value": custom_param}
        )
```