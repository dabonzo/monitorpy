# MonitorPy Demo App

This is a simple web application to demonstrate the MonitorPy API functionality. The app allows you to:

- View available monitoring plugins
- Create and configure monitoring checks
- Run checks and view results
- Track check history

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MonitorPy installed and configured
- Required Python packages: `flask`, `flask-sqlalchemy`, `flask-cors` and other API dependencies

### Running the Demo

1. Install the required dependencies:

   ```bash
   # Install Flask and other required packages
   ./setup.sh
   ```

2. Start the demo app with either the mock API or real API:

   ```bash
   # Option 1: Start with mock API (simpler, in-memory storage)
   ./start.sh
   
   # Option 2: Start with real API (production-ready, database storage)
   ./start_with_real_api.sh
   
   # Customize ports if needed
   ./start.sh --api-port 5000 --app-port 8080
   
   # Specify database URL for real API
   ./start_with_real_api.sh --database "sqlite:///path/to/database.db"
   ```

2. Open your browser and navigate to:
   - Demo App: http://localhost:8080
   - API Base URL: http://localhost:5000

## Features

This demo app provides a simple interface for:

- **Check Management**: Add, delete, and run monitoring checks
- **Plugin Discovery**: View available monitoring plugins and their configuration options
- **Result Viewing**: See recent check results in a table
- **Real-time Testing**: Run checks on demand and see the results immediately

> **Note:** The demo app can run with either:
>
> 1. **Mock API** (default): Uses a simplified API that simulates the full functionality with in-memory storage.
> 2. **Real API**: Uses the actual MonitorPy API implementation with a database backend.
>
> Use `./start.sh` for the mock API or `./start_with_real_api.sh` for the real API.

## Implementation Details

The demo app is a simple client-side JavaScript application that communicates with the MonitorPy API. It includes:

- **index.html**: Main application structure and layout
- **styles.css**: Visual styling for the application
- **app.js**: Application logic and API communication

The app uses modern JavaScript (fetch API, async/await) and does not require any additional libraries or frameworks.

## Cross-Origin Resource Sharing (CORS)

The MonitorPy API has CORS enabled to allow requests from this demo app. If you experience CORS issues:

1. Ensure the API's CORS settings are properly configured
2. Run both the API and the demo app on the same origin or use a CORS proxy

## Known Limitations

This is a simple demo application with the following limitations:

- No authentication or security features
- Limited error handling
- Basic UI with minimal styling
- No pagination for large result sets

For a production deployment, consider building a more robust frontend application.

## Troubleshooting

If you encounter issues:

- Check that the API is running and accessible
- Look for JavaScript errors in the browser console
- Verify that the API URL in `app.js` matches your API deployment
- Ensure all required API dependencies are installed