# Sample Plugin Configuration

The sample plugin provides a demonstration of the plugin framework capabilities. This plugin is intended to serve as an example for developers creating their own plugins.

## Basic Configuration

Here's a basic configuration example for the sample monitor plugin:

```yaml
checks:
  - type: sample_monitor
    name: demo_check
    target: example.com
    check_interval: 60
    timeout: 30
    retry_count: 3
    warning_threshold: 5.0
```

## Configuration Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `target` | string | The target to monitor (e.g., hostname, URL, or other identifier) |
| `check_interval` | number | The interval between checks in seconds |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | number | 30 | Maximum time to wait for response in seconds |
| `retry_count` | integer | 0 | Number of retry attempts before marking as failed |
| `warning_threshold` | number | 5.0 | Response time threshold for warning status in seconds |

## Custom API Monitor Configuration

The framework also includes a specialized API monitoring plugin that extends the sample plugin:

```yaml
checks:
  - type: custom_api_monitor
    name: api_check
    target: api.example.com
    check_interval: 300
    api_key: YOUR_API_KEY
    endpoint: /v1/status
    headers:
      Accept: application/json
      X-Custom-Header: value
    query_params:
      format: json
      verbose: true
```

### Additional Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `api_key` | string | Authentication key for the API |
| `endpoint` | string | The API endpoint to monitor |

### Additional Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `headers` | object | `{}` | Custom HTTP headers to include in requests |
| `query_params` | object | `{}` | Query parameters to include in requests |

## Advanced Configuration Examples

For more advanced configuration examples, see the [Examples](examples.md) documentation.