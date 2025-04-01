# MonitorPy Laravel Integration Guide

This documentation provides a comprehensive guide for integrating MonitorPy's monitoring API with Laravel applications. It covers setup, authentication, endpoints, data models, and practical examples.

## Table of Contents

1. [Overview](#overview)
2. [API Reference](api-reference.md)
3. [Authentication](authentication.md)
4. [Configuration Options](configuration.md)
5. [Data Models](data-models.md)
6. [Integration Examples](examples.md)
7. [Troubleshooting](troubleshooting.md)

## Overview

MonitorPy is a plugin-based monitoring system that provides:

- Website availability and content monitoring
- SSL certificate validity checking
- Mail server monitoring
- DNS record verification
- Flexible plugin architecture for custom monitoring needs

The API allows you to:

- Create and manage monitoring checks
- Retrieve monitoring results
- Get plugin information
- Configure alerts and notifications
- Generate reports and statistics

## Quick Start

For Laravel developers, here's how to quickly set up integration with MonitorPy:

1. Install the Laravel HTTP client:
   ```bash
   composer require guzzlehttp/guzzle
   ```

2. Create an API service provider:
   ```bash
   php artisan make:provider MonitorPyServiceProvider
   ```

3. Configure your MonitorPy API endpoint in `.env`:
   ```
   MONITORPY_API_URL=http://your-monitorpy-server:5000
   MONITORPY_API_KEY=your_api_key
   ```

4. Create a MonitorPy facade or service class for easy access in your application.

5. Use the API in your controllers, jobs, or commands.

## Key Features

- **RESTful API**: Simple JSON-based API for all monitoring functionality
- **Authentication**: JWT-based authentication with role-based access control
- **Pagination**: Efficient data retrieval with pagination support
- **Filtering**: Filter results based on various parameters
- **Real-time Updates**: Webhook support for real-time notifications
- **Batch Operations**: Perform multiple operations in a single request

See the detailed documentation sections for complete information on using MonitorPy with Laravel applications.