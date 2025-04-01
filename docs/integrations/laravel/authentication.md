# Authentication with MonitorPy API

This document explains how to authenticate with the MonitorPy API from your Laravel application.

## Authentication Methods

MonitorPy supports two authentication methods:

1. **JWT Authentication**: Token-based authentication using JSON Web Tokens
2. **API Key Authentication**: Simple API key authentication for services and automation

## JWT Authentication

JWT is the recommended authentication method for user-facing applications.

### Obtaining a JWT Token

```
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Logged in successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### Laravel Implementation

Here's how to implement JWT authentication in your Laravel application:

1. Create a service class to handle MonitorPy authentication:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class MonitorPyService
{
    protected $baseUrl;
    protected $token;
    
    public function __construct()
    {
        $this->baseUrl = config('monitorpy.api_url');
    }
    
    public function login($email, $password)
    {
        $response = Http::post("{$this->baseUrl}/auth/login", [
            'email' => $email,
            'password' => $password,
        ]);
        
        if ($response->successful()) {
            $data = $response->json()['data'];
            $this->token = $data['access_token'];
            
            // Cache token for later use
            Cache::put('monitorpy_token', $this->token, now()->addSeconds($data['expires_in']));
            
            return true;
        }
        
        return false;
    }
    
    public function getToken()
    {
        // Get token from cache if available
        if (!$this->token) {
            $this->token = Cache::get('monitorpy_token');
        }
        
        return $this->token;
    }
    
    public function request($method, $endpoint, $data = [])
    {
        $token = $this->getToken();
        
        if (!$token) {
            throw new \Exception('Not authenticated with MonitorPy API');
        }
        
        $response = Http::withToken($token)
            ->$method("{$this->baseUrl}{$endpoint}", $data);
            
        return $response->json();
    }
    
    // Add more specific methods as needed
}
```

2. Create a MonitorPy config file:

```php
// config/monitorpy.php
return [
    'api_url' => env('MONITORPY_API_URL', 'http://localhost:5000'),
    'api_key' => env('MONITORPY_API_KEY'),
];
```

3. Use the service in your controller:

```php
<?php

namespace App\Http\Controllers;

use App\Services\MonitorPyService;
use Illuminate\Http\Request;

class MonitorPyController extends Controller
{
    protected $monitorPy;
    
    public function __construct(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    public function login(Request $request)
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);
        
        $success = $this->monitorPy->login(
            $request->input('email'),
            $request->input('password')
        );
        
        if ($success) {
            return redirect()->route('dashboard')->with('success', 'Logged in to MonitorPy');
        }
        
        return back()->withErrors(['email' => 'Invalid credentials']);
    }
    
    public function dashboard()
    {
        $checks = $this->monitorPy->request('get', '/checks');
        
        return view('monitorpy.dashboard', [
            'checks' => $checks['data']['checks'] ?? [],
        ]);
    }
}
```

### Token Refresh

JWT tokens expire after a set time. To refresh the token:

```
POST /auth/refresh
```

**Headers:**
```
Authorization: Bearer your_current_token
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

## API Key Authentication

For automated tasks or service-to-service communication, you can use API keys.

### Creating an API Key

API keys can be created in the MonitorPy dashboard or via the API:

```
POST /auth/api-keys
```

**Headers:**
```
Authorization: Bearer your_jwt_token
```

**Request Body:**
```json
{
  "name": "Laravel Integration",
  "expires_at": "2024-12-31T23:59:59Z"  // Optional
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "API key created successfully",
  "data": {
    "id": 5,
    "name": "Laravel Integration",
    "key": "mp_api_b8f7a9c2d6e5f0...",  // Note: shown only once
    "created_at": "2023-05-31T12:30:45Z",
    "expires_at": "2024-12-31T23:59:59Z"
  }
}
```

### Using API Keys in Laravel

To use API key authentication:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class MonitorPyApiService
{
    protected $baseUrl;
    protected $apiKey;
    
    public function __construct()
    {
        $this->baseUrl = config('monitorpy.api_url');
        $this->apiKey = config('monitorpy.api_key');
    }
    
    public function request($method, $endpoint, $data = [])
    {
        $response = Http::withHeaders([
            'X-API-Key' => $this->apiKey,
        ])->$method("{$this->baseUrl}{$endpoint}", $data);
            
        return $response->json();
    }
}
```

## Best Practices

1. **Store tokens securely**: Never expose JWT tokens or API keys in client-side code.

2. **Handle token expiration**: Implement token refresh logic to handle expired tokens.

3. **Use middleware**: Create Laravel middleware to automatically handle authentication.

4. **Implement caching**: Cache tokens to reduce authentication requests.

5. **Use environment variables**: Store API URLs and keys in environment variables.

## Middleware Example

Create a middleware to automatically handle MonitorPy authentication:

```php
<?php

namespace App\Http\Middleware;

use Closure;
use App\Services\MonitorPyService;

class MonitorPyAuth
{
    protected $monitorPy;
    
    public function __construct(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    public function handle($request, Closure $next)
    {
        if (!$this->monitorPy->getToken()) {
            // Redirect to login or return error
            return redirect()->route('monitorpy.login');
        }
        
        return $next($request);
    }
}
```

Register the middleware in `app/Http/Kernel.php`:

```php
protected $routeMiddleware = [
    // Other middleware...
    'monitorpy.auth' => \App\Http\Middleware\MonitorPyAuth::class,
];
```

Use it in your routes:

```php
Route::middleware('monitorpy.auth')
    ->prefix('monitorpy')
    ->group(function () {
        Route::get('/dashboard', [MonitorPyController::class, 'dashboard'])
            ->name('monitorpy.dashboard');
        // Other routes...
    });
```