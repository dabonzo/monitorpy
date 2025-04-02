# MonitorPy Documentation

Welcome to the MonitorPy documentation. MonitorPy is a flexible and extensible monitoring system designed to check website availability, SSL certificate validity, mail server functionality, DNS records, and more.

## Getting Started

- [Getting Started Guide](getting_started.md) - Installation and basic usage
- [Writing Plugins](writing_plugins.md) - Creating custom monitoring plugins

## Monitoring Plugins

MonitorPy includes several built-in monitoring plugins:

### Website Monitoring

Monitor website availability, response codes, and content.

- [Overview](plugins/website/index.md) - Website monitoring capabilities
- [Configuration](plugins/website/configuration.md) - Configuration options
- [Examples](plugins/website/examples.md) - Usage examples
- [Advanced Usage](plugins/website/advanced.md) - Advanced techniques

### SSL Certificate Monitoring

Check SSL certificate validity, expiration, and security.

- [Overview](plugins/ssl/index.md) - SSL monitoring capabilities
- [Configuration](plugins/ssl/configuration.md) - Configuration options
- [Examples](plugins/ssl/examples.md) - Usage examples
- [Advanced Usage](plugins/ssl/advanced.md) - Advanced techniques

### Mail Server Monitoring

Verify mail server functionality and connectivity.

- [Overview](plugins/mail/index.md) - Mail server monitoring capabilities
- [Configuration](plugins/mail/configuration.md) - Configuration options
- [Examples](plugins/mail/examples.md) - Usage examples
- [Advanced Usage](plugins/mail/advanced.md) - Advanced techniques

### DNS Monitoring

Check DNS records, propagation, and DNSSEC validation.

- [Overview](plugins/dns/index.md) - DNS monitoring capabilities
- [Configuration](plugins/dns/configuration.md) - Configuration options
- [Examples](plugins/dns/examples.md) - Usage examples
- [Advanced Usage](plugins/dns/advanced.md) - Advanced techniques

## Command Line Interface

MonitorPy provides a powerful command-line interface for all monitoring functions:

- [Website Commands](cli/website.md) - Website monitoring commands
- [SSL Commands](cli/ssl.md) - SSL certificate monitoring commands
- [Mail Server Commands](cli/mail.md) - Mail server monitoring commands
- [DNS Commands](cli/dns.md) - DNS monitoring commands


## Reference

- [Advanced Configuration Guide](reference/advanced_configuration.md) - Comprehensive configuration options and techniques
- [Configuration Reference](reference/configuration.md) - Complete configuration options
- [User Management](reference/user_management.md) - Managing users and API authentication
- [Redis Integration](reference/redis_usage.md) - Using Redis for caching and background tasks
- [CLI Reference](reference/cli_commands.md) - All command-line options
- [Examples Reference](reference/examples.md) - Common usage patterns

## Development

- [Architecture](development/architecture_notes.md) - System architecture overview
- [API Modernization](development/api_modernization.md) - FastAPI implementation details
- [Plugin System](development/plugin_system.md) - How the plugin system works
- [Docker Usage](development/docker_usage.md) - Using MonitorPy with Docker
- [Testing](testing/index.md) - Testing the monitoring system

## Project Information

- [GitHub Repository](https://github.com/yourusername/monitorpy)
- [License](https://github.com/yourusername/monitorpy/blob/main/LICENSE) - MIT License