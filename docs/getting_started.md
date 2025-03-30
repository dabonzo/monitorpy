# Getting Started with MonitorPy

This guide will help you get started with MonitorPy, a plugin-based website and service monitoring system.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Methods

#### Using pip (future)

```bash
pip install monitorpy
```

#### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/monitorpy_v2.git
cd monitorpy_v2/monitorpy

# Install in development mode
pip install -e .
```

#### Using a virtual environment (recommended)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Navigate to the package directory
cd monitorpy_v2/monitorpy

# Install MonitorPy
pip install -e .
```

## Project Structure

The MonitorPy project follows this directory structure:

```
monitorpy_v2/                # Project root
├── monitorpy/               # Package root (contains setup.py)
│   └── monitorpy/           # Actual package directory
│       ├── __init__.py
│       ├── cli.py
│       ├── core/            # Core components
│       ├── plugins/         # Plugin implementations
│       └── utils/           # Utility functions
└── docs/                    # Documentation
```

This structure allows MonitorPy to be installed as a proper Python package while keeping the project organized.

## Basic Usage

After installation, you can use MonitorPy through its command-line interface.

### Checking a Website

To check if a website is accessible:

```bash
monitorpy website https://www.example.com
```

This will perform a basic check to see if the website responds with a 200 OK status code.

### Checking an SSL Certificate

To check the validity and expiration of an SSL certificate:

```bash
monitorpy ssl www.example.com
```

This will verify if the SSL certificate is valid and report how many days until it expires.

### Listing Available Plugins

To see all available monitoring plugins:

```bash
monitorpy list
```

## Next Steps

- See [CLI Usage](cli_usage.md) for more detailed command-line options
- Learn about [Configuration](configuration.md) options for monitoring checks
- Explore [Examples](examples.md) for common monitoring scenarios
- Learn how to [Write Your Own Plugins](writing_plugins.md) to extend MonitorPy's functionality
