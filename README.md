# MonitorPy

A plugin-based website and service monitoring system.

## Overview

MonitorPy is a flexible and extensible monitoring system designed to check website availability, SSL certificate validity, mail server functionality, and more. It features a plugin architecture that makes it easy to add new monitoring capabilities.

## Features

- Website availability and content monitoring
- SSL certificate validity and expiration checks
- Mail server connectivity and authentication testing
- DNS record checking and propagation monitoring
- Parallel execution for monitoring multiple endpoints simultaneously
- Batch processing for handling large numbers of checks
- Plugin-based architecture for extensibility
- Command-line interface for easy use
- Detailed logging and reporting

## Project Structure

The project follows this directory structure:

```
monitorpy_v2/                # Project root
├── monitorpy/               # Package directory
│   ├── monitorpy/           # Main package source
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── core/            # Core components
│   │   │   ├── batch_runner.py  # Parallel execution system
│   │   │   ├── plugin_base.py   # Plugin base classes
│   │   │   ├── registry.py      # Plugin registry
│   │   │   └── result.py        # Check result classes
│   │   ├── plugins/         # Plugin implementations
│   │   └── utils/           # Utility functions
│   └── tests/               # Test suite
└── docs/                    # Documentation
```

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/dabonzo/monitorpy.git
cd monitorpy

# Install in development mode
pip install -e .
```

### Using pip (future)

```bash
pip install monitorpy
```

### Using Docker

The easiest way to get started is with Docker:

```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/dabonzo/monitorpy:latest

# Or from Docker Hub
docker pull bonzodock/monitorpy:latest

# Run the container
docker run -p 8000:8000 bonzodock/monitorpy:latest

# Authentication is pre-configured with:
# - Username: admin
# - Email: admin@example.com
# - Password: adminpassword
# - API key: automatically generated and displayed at startup
```

MonitorPy images are automatically built and published to both GitHub Container Registry and Docker Hub whenever changes are pushed to the main branch or a new version tag is created.

For more detailed Docker instructions, including environment variables and production best practices, see [DOCKER.md](DOCKER.md)

## Quick Start

After installation, you can use the `monitorpy` command to access the monitoring functions:

```bash
# List available plugins
monitorpy list

# Check a website
monitorpy website https://www.example.com

# Check an SSL certificate
monitorpy ssl www.example.com

# Check a mail server
monitorpy mail example.com --protocol smtp --basic-check --resolve-mx

# Check a DNS record
monitorpy dns example.com --type A --check-propagation

# Check multiple websites in parallel
monitorpy website --sites websites.txt --parallel --max-workers 10

# Run a batch of different checks
monitorpy batch checks.json --max-workers 20 --batch-size 10
```


## Documentation

For detailed documentation, see the [docs](docs/) directory:

- [Getting Started](docs/getting_started.md) - Installation and basic usage
- [CLI Usage](docs/cli_usage.md) - Command-line interface reference
- [Configuration](docs/configuration.md) - Basic configuration options
- [Advanced Configuration](docs/reference/advanced_configuration.md) - Comprehensive configuration guide
- [Examples](docs/examples.md) - Common usage patterns
- [Parallel Execution](docs/parallel/overview.md) - Running checks in parallel
- [Parallel Examples](docs/parallel/examples.md) - Examples of parallel execution usage
- [Writing Plugins](docs/writing_plugins.md) - Extending MonitorPy with custom plugins

## Testing

MonitorPy includes a comprehensive test suite to ensure reliable operation across different environments and scenarios. The tests use pytest and cover all core components and plugins.

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Generate coverage report
pytest --cov=monitorpy tests/
```

### Test Documentation

For detailed information about the testing approach and test suite organization, see the [Testing Documentation](docs/testing/index.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
