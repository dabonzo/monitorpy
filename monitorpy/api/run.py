"""
Development server for the MonitorPy API.

This script runs the Flask development server for testing.
"""

import os
from monitorpy.api import create_app
from monitorpy.api.config import get_config

# Set development environment if not specified
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'development'

app = create_app(get_config())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)