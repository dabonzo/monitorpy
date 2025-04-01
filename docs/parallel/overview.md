# MonitorPy Parallel Execution

MonitorPy supports parallel execution of monitoring checks, allowing you to efficiently monitor large numbers of endpoints simultaneously.

## Overview

The parallel execution system uses Python's `ThreadPoolExecutor` to run checks concurrently, which is particularly useful for:

- Monitoring large numbers of websites
- Checking SSL certificates across many domains
- Verifying mail server functionality for multiple servers
- Running DNS checks for many domains

## Core Components

MonitorPy implements parallel execution through two key components:

1. **Batch Runner**: A core module for running multiple checks in parallel
2. **Batch API**: An API endpoint for executing checks concurrently and returning results

## Using Parallel Execution from the CLI

The command-line interface supports parallel execution in two ways:

### 1. Batch Command

The `batch` command allows you to run multiple checks from a JSON configuration file:

```bash
monitorpy batch checks.json --max-workers 20 --batch-size 10
```

Where `checks.json` contains an array of check configurations:

```json
[
  {
    "id": "web1", 
    "plugin_type": "website_status",
    "config": {
      "url": "https://example.com",
      "timeout": 30
    }
  },
  {
    "id": "ssl1",
    "plugin_type": "ssl_certificate",
    "config": {
      "hostname": "example.com",
      "warning_days": 30
    }
  }
]
```

### 2. Parallel Flag with List Files

You can use the `--parallel` flag with any of the main check commands (`website`, `ssl`, `mail`, `dns`), combined with a file list:

```bash
# Check multiple websites in parallel
monitorpy website --sites websites.txt --parallel --max-workers 10

# Check multiple SSL certificates in parallel
monitorpy ssl --hosts hostnames.txt --parallel --max-workers 10

# Check multiple mail servers in parallel
monitorpy mail --servers mailservers.txt --parallel --max-workers 10

# Check multiple domains' DNS records in parallel
monitorpy dns --domains domains.txt --parallel --max-workers 10
```

Each file should contain one item per line:

```
example.com
example.org
another-site.com
```

## Using Parallel Execution with the API

The API provides a batch execution endpoint:

```
POST /api/v1/batch/run
```

Request body:

```json
{
  "checks": ["check_id_1", "check_id_2", "check_id_3"],
  "max_workers": 10,
  "timeout": 60
}
```

For running ad-hoc checks without storing them:

```
POST /api/v1/batch/run-ad-hoc
```

Request body:

```json
{
  "checks": [
    {
      "plugin_type": "website_status",
      "config": {
        "url": "https://example.com"
      }
    },
    {
      "plugin_type": "ssl_certificate",
      "config": {
        "hostname": "example.org"
      }
    }
  ],
  "max_workers": 10,
  "timeout": 60
}
```

## Using Parallel Execution in Python Code

You can use the parallel execution system directly in your Python code:

```python
from monitorpy.core import run_checks_in_parallel, run_check_batch

# Define check configurations
check_configs = [
    {
        "id": "web1",
        "plugin_type": "website_status",
        "config": {
            "url": "https://example.com"
        }
    },
    {
        "id": "ssl1",
        "plugin_type": "ssl_certificate",
        "config": {
            "hostname": "example.org"
        }
    }
]

# Run checks in parallel with up to 10 worker threads
results = run_checks_in_parallel(check_configs, max_workers=10)

# Process results
for check_config, result in results:
    print(f"Check {check_config['id']}: {result.status} - {result.message}")
```

For larger batches, you can use the batch runner:

```python
results = run_check_batch(check_configs, batch_size=10, max_workers=5)
```

## Performance Considerations

1. **Threads vs. Processes**: MonitorPy uses threads rather than processes because monitoring checks are typically I/O-bound rather than CPU-bound.

2. **Number of Workers**: The default worker count is `min(32, os.cpu_count() + 4)`, which is usually a good balance. For very large numbers of checks, you might want to limit this to avoid overwhelming network resources.

3. **Batch Size**: For extremely large numbers of checks (hundreds or thousands), it's better to use `run_check_batch` which processes checks in smaller batches to manage memory usage.

4. **Timeouts**: Always set a reasonable timeout for batch operations to avoid hanging indefinitely if a single check never completes.

5. **Resource Usage**: Monitoring many endpoints simultaneously may require more system resources, particularly network connections and memory.

## Error Handling

The parallel execution system includes robust error handling:

- Exceptions in individual checks won't affect other checks
- Timeouts can be set to prevent hanging operations
- All errors are properly logged for diagnosis

If a check fails due to an exception, the result will have an `error` status with details about the exception in the `raw_data` field.

## Example: Monitoring Website Uptime

Here's a complete example of checking multiple websites in parallel:

```python
from monitorpy.core import run_checks_in_parallel
import json

# List of websites to check
websites = [
    "https://example.com",
    "https://example.org",
    "https://example.net"
]

# Create check configurations
check_configs = [
    {
        "id": f"site{i+1}",
        "plugin_type": "website_status",
        "config": {
            "url": url,
            "timeout": 30,
            "expected_status": 200
        }
    }
    for i, url in enumerate(websites)
]

# Run checks in parallel
results = run_checks_in_parallel(check_configs)

# Calculate statistics
total = len(results)
success = sum(1 for _, result in results if result.status == "success")
warning = sum(1 for _, result in results if result.status == "warning")
error = sum(1 for _, result in results if result.status == "error")

print(f"Summary: {success}/{total} successful, {warning} warnings, {error} errors")

# Output detailed results
for check_config, result in results:
    print(f"\nSite: {check_config['config']['url']}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Response Time: {result.response_time:.3f}s")
```

## Example: Batch API Integration

Example of using the batch API endpoint from an external application:

```javascript
// Using fetch in JavaScript
async function checkMultipleEndpoints() {
  const response = await fetch('http://monitorpy-server:5000/api/v1/batch/run-ad-hoc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer your_jwt_token'
    },
    body: JSON.stringify({
      checks: [
        {
          plugin_type: 'website_status',
          config: {
            url: 'https://example.com'
          }
        },
        {
          plugin_type: 'website_status',
          config: {
            url: 'https://example.org'
          }
        }
      ],
      max_workers: 10
    })
  });

  const data = await response.json();
  console.log('Results:', data.results);
}
```

## Conclusion

Parallel execution makes MonitorPy highly scalable and efficient for monitoring large numbers of endpoints. By running checks concurrently, you can significantly reduce the total time needed for comprehensive monitoring while maintaining accuracy and reliability.