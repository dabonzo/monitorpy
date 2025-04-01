# MonitorPy Troubleshooting

This document provides solutions to common issues when integrating MonitorPy with Laravel applications.

## Authentication Issues

### JWT Token Issues

**Problem**: Authentication fails with "Invalid credentials" or "Token expired" errors.

**Solutions**:

1. **Check credentials**: Verify that the email and password in your config match a valid MonitorPy user.

2. **Token expiration**: JWT tokens expire after a set time (default 1 hour). Implement token refresh:

   ```php
   if ($response->status() === 401) {
       // Token expired - get a new one
       Cache::forget('monitorpy_token');
       $this->token = null;
       $this->login();
       
       // Retry the request
       return $this->request($method, $endpoint, $data);
   }
   ```

3. **CORS issues**: If your Laravel app and MonitorPy API are on different domains:

   ```php
   // In MonitorPy API server .env file
   ALLOWED_ORIGINS=https://your-laravel-app.com
   ```

### API Key Issues

**Problem**: API requests fail with 403 Forbidden errors.

**Solutions**:

1. **Verify key**: Check that the API key exists and is active in MonitorPy.

2. **Header format**: Ensure the API key is sent in the correct header format:

   ```php
   $response = Http::withHeaders([
       'X-API-Key' => config('monitorpy.api_key'),
   ])->get('http://monitorpy-api/checks');
   ```

3. **Permissions**: Verify the API key has the necessary permissions for the endpoints you're accessing.

## Connection Issues

### API Unreachable

**Problem**: Cannot connect to the MonitorPy API server.

**Solutions**:

1. **Check URL**: Verify the API URL in your `.env` file:

   ```
   MONITORPY_API_URL=http://monitorpy-api:5000
   ```

2. **Network connectivity**: Check that your Laravel app can reach the MonitorPy server:

   ```bash
   curl -v http://monitorpy-api:5000/health
   ```

3. **Firewall issues**: Ensure firewalls are not blocking the connection.

4. **Try different protocols**: If using HTTPS, try HTTP to isolate SSL-related issues.

### Timeout Issues

**Problem**: Requests to MonitorPy API time out.

**Solutions**:

1. **Increase timeout**: Set a longer timeout for API requests:

   ```php
   $response = Http::timeout(60)->get('http://monitorpy-api/checks');
   ```

2. **Check server load**: If MonitorPy is under heavy load, it may respond slowly.

3. **Connection pooling**: For high-volume applications, implement connection pooling:

   ```php
   // Create a persistent HTTP client
   $client = Http::pool(function ($pool) {
       return [
           $pool->as('checks')->get('http://monitorpy-api/checks'),
           $pool->as('results')->get('http://monitorpy-api/results'),
       ];
   });
   
   $checks = $client['checks']->json();
   $results = $client['results']->json();
   ```

## Data Issues

### Stale Data

**Problem**: Your Laravel application shows outdated monitoring data.

**Solutions**:

1. **Review caching**: Check if you're caching results for too long:

   ```php
   // Reduce cache time
   Cache::remember('monitorpy_dashboard', 60, function () {
       return $this->getDashboardData();
   });
   ```

2. **Force refresh**: Add a manual refresh option:

   ```php
   public function refreshData()
   {
       Cache::forget('monitorpy_dashboard');
       $this->emit('dataRefreshed');
   }
   ```

3. **Implement webhooks**: Use MonitorPy webhooks to update data in real-time.

### Inconsistent Data

**Problem**: Data in your Laravel app doesn't match what's shown in MonitorPy.

**Solutions**:

1. **Sync implementation**: Implement a proper sync service:

   ```php
   // In a scheduled task
   $monitorPyService->syncAllData();
   ```

2. **Data validation**: Validate incoming webhook data:

   ```php
   // In webhook handler
   if (!isset($payload['data']['id']) || !isset($payload['data']['status'])) {
       return response()->json(['error' => 'Invalid payload format'], 400);
   }
   ```

3. **Log discrepancies**: Log when data doesn't match expectations:

   ```php
   Log::warning('Inconsistent data from MonitorPy', [
       'local_record' => $localCheck,
       'api_response' => $apiCheck,
   ]);
   ```

## Performance Issues

### Slow API Responses

**Problem**: MonitorPy API responses are slow, affecting your Laravel app.

**Solutions**:

1. **Batch requests**: Use the batch endpoint to combine multiple operations:

   ```php
   $response = $monitorPy->request('post', '/batch', [
       'operations' => [
           ['method' => 'GET', 'path' => '/checks/1'],
           ['method' => 'GET', 'path' => '/checks/2'],
       ],
   ]);
   ```

2. **Implement caching**: Cache frequently accessed data:

   ```php
   $plugins = Cache::remember('monitorpy_plugins', 3600, function () {
       return $this->monitorPy->getPlugins();
   });
   ```

3. **Background processing**: Move non-critical operations to background jobs:

   ```php
   // In controller
   SyncMonitorPyDataJob::dispatch();
   
   // In job class
   public function handle(MonitorPyService $monitorPy)
   {
       $monitorPy->syncAllData();
   }
   ```

### High CPU Usage

**Problem**: Frequent polling of the MonitorPy API causes high resource usage.

**Solutions**:

1. **Reduce polling frequency**: Increase intervals between checks:

   ```php
   // In Livewire component
   public $pollingInterval = 60000; // 1 minute instead of 10 seconds
   ```

2. **Selective polling**: Only poll for critical checks:

   ```php
   public function getRefreshInterval()
   {
       return $this->showCriticalOnly ? 10000 : 60000;
   }
   ```

3. **Use webhooks**: Replace polling with webhook notifications.

## Webhook Issues

### Missing Webhook Events

**Problem**: Your Laravel app isn't receiving webhook events from MonitorPy.

**Solutions**:

1. **Verify registration**: Ensure webhooks are properly registered:

   ```php
   $monitorPy->request('post', '/webhooks', [
       'url' => 'https://your-laravel-app.com/api/webhooks/monitorpy',
       'events' => ['check.result', 'check.created', 'check.updated'],
       'secret' => config('monitorpy.webhook_token'),
   ]);
   ```

2. **Check logs**: Verify MonitorPy is sending webhooks by checking its logs.

3. **Test endpoint**: Ensure your webhook endpoint is publicly accessible:

   ```bash
   curl -X POST https://your-laravel-app.com/api/webhooks/monitorpy \
     -d '{"event":"test"}' \
     -H "Content-Type: application/json"
   ```

### Invalid Webhook Signatures

**Problem**: Webhook requests fail signature validation.

**Solutions**:

1. **Check secret**: Ensure the webhook secret matches on both sides:

   ```php
   // In middleware
   $secret = config('monitorpy.webhook_token');
   $signature = hash_hmac('sha256', $request->getContent(), $secret);
   
   if (!hash_equals($expectedSignature, $signature)) {
       Log::warning('Invalid webhook signature', [
           'expected' => $expectedSignature,
           'received' => $signature,
       ]);
       
       return response()->json(['error' => 'Invalid signature'], 403);
   }
   ```

2. **Debug headers**: Log all webhook headers to identify issues:

   ```php
   Log::debug('Webhook headers', $request->headers->all());
   ```

3. **Disable validation temporarily**: For testing, temporarily disable signature validation.

## Database Migration Issues

### Model Compatibility Issues

**Problem**: MonitorPy data structure doesn't map cleanly to your Laravel models.

**Solutions**:

1. **Use casts**: Convert data types automatically:

   ```php
   protected $casts = [
       'config' => 'array',
       'raw_data' => 'array',
       'executed_at' => 'datetime',
   ];
   ```

2. **Implement accessors/mutators**: Transform data as needed:

   ```php
   public function getStatusBadgeAttribute()
   {
       return match($this->status) {
           'success' => 'badge-success',
           'warning' => 'badge-warning',
           'error' => 'badge-danger',
           default => 'badge-secondary',
       };
   }
   ```

3. **Use database views**: Create views that transform data into your preferred format.

### Missing Fields

**Problem**: MonitorPy API returns fields not present in your database.

**Solutions**:

1. **Use migrations**: Update your database schema to match the API:

   ```php
   Schema::table('monitoring_checks', function (Blueprint $table) {
       $table->json('additional_data')->nullable();
   });
   ```

2. **Store as JSON**: Use JSON columns for dynamic data:

   ```php
   $check->metadata = json_encode($apiData);
   ```

3. **Selective sync**: Only store fields relevant to your application.

## Integration Testing

### Mocking the MonitorPy API

For testing Laravel applications that integrate with MonitorPy without calling the actual API:

```php
<?php

namespace Tests\Feature;

use App\Services\MonitorPyService;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class MonitoringTest extends TestCase
{
    public function test_dashboard_displays_checks()
    {
        // Mock API responses
        Http::fake([
            'http://monitorpy-api/checks' => Http::response([
                'status' => 'success',
                'data' => [
                    'checks' => [
                        [
                            'id' => 1,
                            'name' => 'Test Website',
                            'plugin' => 'website_status',
                            'config' => ['url' => 'https://example.com'],
                            'status' => 'active',
                            'last_result' => 'success',
                            'last_run' => now()->toISOString(),
                        ],
                    ],
                ],
                'meta' => [
                    'page' => 1,
                    'per_page' => 20,
                    'total' => 1,
                ],
            ]),
        ]);
        
        $response = $this->get('/monitoring/dashboard');
        
        $response->assertStatus(200);
        $response->assertSee('Test Website');
        $response->assertSee('success');
    }
    
    public function test_creating_new_check()
    {
        // Mock API response
        Http::fake([
            'http://monitorpy-api/checks' => Http::response([
                'status' => 'success',
                'message' => 'Check created successfully',
                'data' => [
                    'id' => 2,
                    'name' => 'New Test Check',
                    'plugin' => 'website_status',
                    'config' => ['url' => 'https://test.com'],
                ],
            ]),
        ]);
        
        $response = $this->post('/monitoring/checks', [
            'name' => 'New Test Check',
            'plugin' => 'website_status',
            'config' => ['url' => 'https://test.com'],
        ]);
        
        $response->assertRedirect('/monitoring/dashboard');
        $response->assertSessionHas('success');
        
        // Verify the request was made correctly
        Http::assertSent(function ($request) {
            return $request->url() == 'http://monitorpy-api/checks' &&
                   $request->method() == 'POST' &&
                   $request['name'] == 'New Test Check';
        });
    }
}
```

## Deployment Issues

### SSL Certificate Verification

**Problem**: API calls fail due to SSL certificate issues.

**Solutions**:

1. **Disable verification** (only for testing):

   ```php
   $client = Http::withOptions([
       'verify' => false,
   ])->get('https://monitorpy-api/checks');
   ```

2. **Add CA certificates**:

   ```php
   $client = Http::withOptions([
       'verify' => '/path/to/cacert.pem',
   ])->get('https://monitorpy-api/checks');
   ```

3. **Use HTTP** if both services are in the same secure network:

   ```
   MONITORPY_API_URL=http://monitorpy-api:5000
   ```

### Docker Networking Issues

**Problem**: Laravel container cannot reach MonitorPy container.

**Solutions**:

1. **Use Docker network names**:

   ```
   MONITORPY_API_URL=http://monitorpy-service:5000
   ```

2. **Create a Docker network**: Put both containers on the same network:

   ```yaml
   # docker-compose.yml
   networks:
     monitoring_network:
       driver: bridge
   
   services:
     laravel:
       # ...
       networks:
         - monitoring_network
     
     monitorpy:
       # ...
       networks:
         - monitoring_network
   ```

3. **Check Docker DNS**: Ensure DNS resolution works within the container:

   ```bash
   docker exec -it laravel-container ping monitorpy-service
   ```

## Error Handling Best Practices

```php
try {
    $result = $monitorPy->request('get', '/checks');
    
    if (isset($result['status']) && $result['status'] === 'error') {
        Log::error('MonitorPy API returned error', [
            'message' => $result['message'] ?? 'Unknown error',
            'data' => $result['data'] ?? null,
        ]);
        
        return $this->handleApiError($result);
    }
    
    return $result;
} catch (\Illuminate\Http\Client\ConnectionException $e) {
    Log::error('MonitorPy API connection error', [
        'message' => $e->getMessage(),
    ]);
    
    return $this->handleConnectionError($e);
} catch (\Exception $e) {
    Log::error('Unexpected error in MonitorPy integration', [
        'message' => $e->getMessage(),
        'trace' => $e->getTraceAsString(),
    ]);
    
    return $this->handleUnexpectedError($e);
}
```

## Known Issues and Workarounds

### Rate Limiting

**Issue**: The MonitorPy API enforces rate limits that may affect busy Laravel applications.

**Workaround**: Implement exponential backoff:

```php
public function requestWithRetry($method, $endpoint, $data = [], $attempt = 1)
{
    $response = $this->request($method, $endpoint, $data);
    
    if (isset($response['status']) && $response['status'] === 'error' && 
        strpos($response['message'], 'rate limit') !== false && 
        $attempt < 5) {
        
        // Exponential backoff
        $sleepTime = pow(2, $attempt) * 1000; // Milliseconds
        usleep($sleepTime * 1000); // Convert to microseconds
        
        return $this->requestWithRetry($method, $endpoint, $data, $attempt + 1);
    }
    
    return $response;
}
```

### Data Synchronization

**Issue**: Keeping local Laravel database in sync with MonitorPy can be challenging.

**Workaround**: Implement a "refresh from API" function:

```php
public function refreshFromApi($checkId)
{
    $apiCheck = $this->monitorPy->getCheck($checkId);
    
    if (!$apiCheck) {
        return false;
    }
    
    $localCheck = MonitoringCheck::where('monitorpy_id', $checkId)->first();
    
    if (!$localCheck) {
        // Create a new local record
        $localCheck = new MonitoringCheck();
        $localCheck->monitorpy_id = $checkId;
    }
    
    // Update with data from API
    $localCheck->name = $apiCheck['name'];
    $localCheck->plugin = $apiCheck['plugin'];
    $localCheck->config = $apiCheck['config'];
    $localCheck->status = $apiCheck['status'];
    $localCheck->interval = $apiCheck['interval'] ?? 300;
    $localCheck->last_run = isset($apiCheck['last_run']) ? 
        \Carbon\Carbon::parse($apiCheck['last_run']) : null;
    $localCheck->last_result = $apiCheck['last_result'] ?? null;
    
    $localCheck->save();
    
    return $localCheck;
}
```

## Getting Help

If you encounter issues not covered in this guide:

1. **Check MonitorPy logs**: Review the API server logs for errors.

2. **Enable debug mode**: Increase logging verbosity in both MonitorPy and Laravel.

3. **Contact support**: Reach out to MonitorPy support or community forums.

4. **Contribute**: If you find a solution to a common problem, consider contributing it to this troubleshooting guide.