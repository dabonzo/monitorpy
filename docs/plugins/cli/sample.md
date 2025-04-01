# Sample Plugin CLI Usage

This guide explains how to use the sample monitoring plugins from the command line.

## Sample Monitor

The `sample_monitor` plugin can be used to test the monitoring framework or as a template for custom plugins.

### Basic Usage

```bash
monitorpy check sample_monitor --target example.com --check-interval 60
```

### All Available Options

```bash
monitorpy check sample_monitor \
  --target example.com \
  --check-interval 60 \
  --timeout 30 \
  --retry-count 3 \
  --warning-threshold 5.0
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--target` | The target to monitor | (Required) |
| `--check-interval` | Interval between checks in seconds | (Required) |
| `--timeout` | Maximum wait time in seconds | 30 |
| `--retry-count` | Number of retry attempts | 0 |
| `--warning-threshold` | Threshold for warning status | 5.0 |

## Custom API Monitor

The `custom_api_monitor` plugin demonstrates extending the sample plugin for API monitoring.

### Basic Usage

```bash
monitorpy check custom_api_monitor \
  --target api.example.com \
  --check-interval 60 \
  --api-key YOUR_API_KEY \
  --endpoint /v1/status
```

### All Available Options

```bash
monitorpy check custom_api_monitor \
  --target api.example.com \
  --check-interval 60 \
  --timeout 30 \
  --retry-count 3 \
  --warning-threshold 5.0 \
  --api-key YOUR_API_KEY \
  --endpoint /v1/status \
  --headers '{"Accept": "application/json", "X-Custom-Header": "value"}' \
  --query-params '{"format": "json", "verbose": true}'
```

### Parameters

Includes all parameters from `sample_monitor`, plus:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--api-key` | Authentication key for the API | (Required) |
| `--endpoint` | API endpoint to monitor | (Required) |
| `--headers` | JSON string of custom HTTP headers | `{}` |
| `--query-params` | JSON string of query parameters | `{}` |

## Examples

### Running a Basic Check

```bash
# Basic sample monitor check
monitorpy check sample_monitor --target example.com --check-interval 60

# API monitor check
monitorpy check custom_api_monitor \
  --target api.example.com \
  --check-interval 300 \
  --api-key ABC123 \
  --endpoint /status
```

### Output Format Options

```bash
# Get results in JSON format
monitorpy check sample_monitor --target example.com --check-interval 60 --output json

# Get verbose output
monitorpy check sample_monitor --target example.com --check-interval 60 --verbose
```

### Running Multiple Checks

```bash
# Use a configuration file for multiple checks
monitorpy run --config config.yaml
```

Example `config.yaml`:

```yaml
checks:
  - type: sample_monitor
    name: sample_check
    target: example.com
    check_interval: 60
    
  - type: custom_api_monitor
    name: api_check
    target: api.example.com
    check_interval: 300
    api_key: YOUR_API_KEY
    endpoint: /status
```