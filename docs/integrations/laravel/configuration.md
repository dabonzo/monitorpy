# MonitorPy Configuration Options

This document outlines all available configuration options for MonitorPy when integrating with Laravel applications.

## Laravel Configuration

When integrating MonitorPy with Laravel, you'll need to configure your application to communicate with the MonitorPy API. Below are the recommended configuration steps.

### Configuration File

Create a dedicated configuration file for MonitorPy:

```bash
php artisan vendor:publish --tag=monitorpy-config
```

Or manually create `config/monitorpy.php`:

```php
<?php

return [
    /*
    |--------------------------------------------------------------------------
    | MonitorPy API Configuration
    |--------------------------------------------------------------------------
    */

    // API Base URL
    'api_url' => env('MONITORPY_API_URL', 'http://localhost:5000'),
    
    // Authentication
    'api_key' => env('MONITORPY_API_KEY'),
    'auth_method' => env('MONITORPY_AUTH_METHOD', 'jwt'), // 'jwt' or 'api_key'
    
    // JWT Authentication credentials (if using JWT)
    'auth_email' => env('MONITORPY_AUTH_EMAIL'),
    'auth_password' => env('MONITORPY_AUTH_PASSWORD'),
    
    // Request Configuration
    'timeout' => env('MONITORPY_TIMEOUT', 30),
    'connect_timeout' => env('MONITORPY_CONNECT_TIMEOUT', 10),
    
    // Cache Configuration
    'cache_enabled' => env('MONITORPY_CACHE_ENABLED', true),
    'cache_ttl' => env('MONITORPY_CACHE_TTL', 300), // 5 minutes
    
    // Webhook Configuration (if receiving MonitorPy webhooks)
    'webhook_token' => env('MONITORPY_WEBHOOK_TOKEN'),
    'webhook_url' => env('APP_URL') . '/api/monitorpy/webhook',
    
    // Plugin Default Configuration
    'plugins' => [
        'website_status' => [
            'timeout' => 30,
            'expected_status' => 200,
            'follow_redirects' => true,
        ],
        'ssl_certificate' => [
            'warning_days' => 30,
            'critical_days' => 7,
        ],
        // Add other plugin defaults as needed
    ],
];
```

### Environment Variables

Add the following to your `.env` file:

```
MONITORPY_API_URL=http://your-monitorpy-server:5000
MONITORPY_API_KEY=your_api_key
MONITORPY_AUTH_METHOD=jwt
MONITORPY_AUTH_EMAIL=admin@example.com
MONITORPY_AUTH_PASSWORD=secure_password
MONITORPY_TIMEOUT=30
MONITORPY_CACHE_ENABLED=true
MONITORPY_WEBHOOK_TOKEN=random_secure_token
```

## MonitorPy API Server Configuration

The MonitorPy API server itself has several configuration options that affect how it operates. These settings are managed on the server side, but understanding them is important for integration.

### Server Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///:memory:` |
| `SECRET_KEY` | Secret key for JWT encoding | random (server restart invalidates tokens) |
| `JWT_SECRET_KEY` | Secret key specifically for JWT | Same as SECRET_KEY |
| `JWT_ACCESS_TOKEN_EXPIRES` | JWT token expiration in seconds | 3600 (1 hour) |
| `FLASK_ENV` | Environment (development/production) | `production` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `*` |
| `AUTH_REQUIRED` | Whether authentication is required | `true` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Database Configuration

MonitorPy supports multiple database backends:

**SQLite** (good for development):
```
DATABASE_URL=sqlite:///path/to/monitorpy.db
```

**PostgreSQL** (recommended for production):
```
DATABASE_URL=postgresql://username:password@hostname/database
```

**MySQL**:
```
DATABASE_URL=mysql://username:password@hostname/database
```

## Plugin Configuration

Each monitoring plugin has its own set of configuration options. Below are the most commonly used plugins and their configuration parameters.

### Website Status Plugin

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | | URL to check |
| `timeout` | integer | No | 30 | Request timeout in seconds |
| `expected_status` | integer | No | 200 | Expected HTTP status code |
| `method` | string | No | GET | HTTP method |
| `headers` | object | No | {} | HTTP headers |
| `body` | string | No | | Request body data |
| `auth_username` | string | No | | Basic auth username |
| `auth_password` | string | No | | Basic auth password |
| `verify_ssl` | boolean | No | true | Verify SSL certificates |
| `follow_redirects` | boolean | No | true | Follow HTTP redirects |
| `expected_content` | string | No | | Content that should be present |
| `unexpected_content` | string | No | | Content that should NOT be present |

**Laravel Example:**

```php
$config = [
    'url' => 'https://example.com',
    'timeout' => 30,
    'expected_status' => 200,
    'follow_redirects' => true,
    'expected_content' => 'Welcome to Example',
];

$monitorPy->createCheck('Example Website', 'website_status', $config);
```

### SSL Certificate Plugin

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hostname` | string | Yes | | Hostname to check |
| `port` | integer | No | 443 | Port number |
| `timeout` | integer | No | 30 | Connection timeout in seconds |
| `warning_days` | integer | No | 30 | Warning threshold in days |
| `critical_days` | integer | No | 7 | Critical threshold in days |
| `check_chain` | boolean | No | false | Check certificate chain |
| `verify_hostname` | boolean | No | true | Verify hostname matches certificate |

**Laravel Example:**

```php
$config = [
    'hostname' => 'example.com',
    'warning_days' => 30,
    'critical_days' => 7,
];

$monitorPy->createCheck('Example SSL', 'ssl_certificate', $config);
```

### Mail Server Plugin

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hostname` | string | Yes | | Mail server hostname or domain |
| `protocol` | string | Yes | | Mail protocol (smtp, imap, pop3) |
| `port` | integer | No | | Server port (protocol-specific default) |
| `username` | string | No | | Username for authentication |
| `password` | string | No | | Password for authentication |
| `use_ssl` | boolean | No | false | Use SSL connection |
| `use_tls` | boolean | No | false | Use TLS connection (SMTP only) |
| `timeout` | integer | No | 30 | Connection timeout in seconds |
| `test_send` | boolean | No | false | Send test email (SMTP only) |
| `from_email` | string | No | | From email address (for test email) |
| `to_email` | string | No | | To email address (for test email) |
| `resolve_mx` | boolean | No | true | Resolve MX records for domain |

**Laravel Example:**

```php
$config = [
    'hostname' => 'mail.example.com',
    'protocol' => 'smtp',
    'port' => 587,
    'use_tls' => true,
    'timeout' => 30,
];

$monitorPy->createCheck('Example Mail Server', 'mail_server', $config);
```

### DNS Plugin

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | | Domain name to check |
| `record_type` | string | No | A | DNS record type |
| `expected_value` | string | No | | Expected record value |
| `subdomain` | string | No | | Subdomain to check |
| `nameserver` | string | No | | Specific nameserver to query |
| `timeout` | integer | No | 10 | Query timeout in seconds |
| `check_propagation` | boolean | No | false | Check DNS propagation |
| `threshold` | float | No | 80 | Propagation threshold percentage |

**Laravel Example:**

```php
$config = [
    'domain' => 'example.com',
    'record_type' => 'A',
    'expected_value' => '93.184.216.34',
];

$monitorPy->createCheck('Example DNS', 'dns', $config);
```

## Webhook Configuration

MonitorPy can send webhook notifications to your Laravel application when check statuses change. To configure webhooks:

1. Add a webhook endpoint to your Laravel routes:

```php
Route::post('/api/monitorpy/webhook', [WebhookController::class, 'handle'])
    ->middleware('monitorpy.webhook');
```

2. Create a middleware to validate the webhook:

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class MonitorPyWebhook
{
    public function handle(Request $request, Closure $next)
    {
        $signature = $request->header('X-MonitorPy-Signature');
        $token = config('monitorpy.webhook_token');
        
        // Validate the signature
        $payload = $request->getContent();
        $expected = hash_hmac('sha256', $payload, $token);
        
        if (!hash_equals($expected, $signature)) {
            return response()->json([
                'error' => 'Invalid signature'
            ], 403);
        }
        
        return $next($request);
    }
}
```

3. Handle the webhook in your controller:

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\MonitoringResult;
use App\Events\MonitoringAlert;

class WebhookController extends Controller
{
    public function handle(Request $request)
    {
        $payload = $request->json()->all();
        
        // Process the webhook payload
        if ($payload['event'] === 'check.result') {
            $result = $payload['data'];
            
            // Store the result
            MonitoringResult::create([
                'check_id' => $result['check_id'],
                'status' => $result['status'],
                'message' => $result['message'],
                'response_time' => $result['response_time'],
                'executed_at' => $result['executed_at'],
                'raw_data' => json_encode($result['raw_data']),
            ]);
            
            // Trigger alerts if needed
            if ($result['status'] === 'error') {
                event(new MonitoringAlert($result));
            }
        }
        
        return response()->json(['success' => true]);
    }
}
```

4. Configure the webhook in MonitorPy:

Send a request to register your webhook endpoint:

```php
$monitorPy->request('post', '/webhooks', [
    'url' => config('monitorpy.webhook_url'),
    'events' => ['check.result', 'check.created', 'check.updated'],
    'secret' => config('monitorpy.webhook_token'),
]);
```

## Advanced Configuration

### Custom HTTP Client

You can customize the HTTP client used for API requests:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class MonitorPyService
{
    protected function getClient()
    {
        return Http::withOptions([
            'verify' => true,  // Verify SSL certificates
            'timeout' => config('monitorpy.timeout'),
            'connect_timeout' => config('monitorpy.connect_timeout'),
        ])->withHeaders([
            'User-Agent' => 'Laravel MonitorPy Client/1.0',
            'Accept' => 'application/json',
        ]);
    }
    
    public function request($method, $endpoint, $data = [])
    {
        $client = $this->getClient();
        
        // Add authentication
        if (config('monitorpy.auth_method') === 'jwt') {
            $client = $client->withToken($this->getToken());
        } else {
            $client = $client->withHeaders([
                'X-API-Key' => config('monitorpy.api_key'),
            ]);
        }
        
        return $client->$method(
            config('monitorpy.api_url') . $endpoint, 
            $data
        )->json();
    }
}
```

### Rate Limiting

The MonitorPy API implements rate limiting to prevent abuse. Default limits are:

- 60 requests per minute for authenticated users
- 10 requests per minute for anonymous users

Your integration should handle rate limit responses (HTTP 429) gracefully:

```php
public function request($method, $endpoint, $data = [])
{
    try {
        $response = $this->client->$method($endpoint, $data);
        
        if ($response->status() === 429) {
            // Rate limited - wait and retry
            $retryAfter = $response->header('Retry-After', 60);
            sleep($retryAfter);
            return $this->request($method, $endpoint, $data);
        }
        
        return $response->json();
    } catch (\Exception $e) {
        // Handle other exceptions
    }
}
```

### Bulk Operations

For efficiency, use batch operations when working with multiple checks:

```php
$operations = [
    [
        'method' => 'GET',
        'path' => '/checks/1',
    ],
    [
        'method' => 'GET',
        'path' => '/checks/2',
    ],
];

$results = $monitorPy->request('post', '/batch', ['operations' => $operations]);
```