# MonitorPy Data Models

This document outlines the data models used by the MonitorPy API and provides guidance on mapping them to Laravel models.

## Core Data Models

### Check

Represents a configured monitoring check.

**API Model Structure:**
```json
{
  "id": 1,
  "name": "Example Website",
  "plugin": "website_status",
  "config": {
    "url": "https://example.com",
    "timeout": 30
  },
  "status": "active",
  "interval": 300,
  "last_run": "2023-05-31T14:22:15Z",
  "last_result": "success",
  "created_at": "2023-05-01T09:15:22Z",
  "updated_at": "2023-05-31T14:22:15Z"
}
```

**Laravel Model:**

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MonitoringCheck extends Model
{
    use HasFactory;
    
    protected $fillable = [
        'monitorpy_id',
        'name',
        'plugin',
        'config',
        'status',
        'interval',
        'last_run',
        'last_result',
    ];
    
    protected $casts = [
        'config' => 'array',
        'last_run' => 'datetime',
        'interval' => 'integer',
    ];
    
    public function results()
    {
        return $this->hasMany(MonitoringResult::class, 'check_id', 'monitorpy_id');
    }
    
    public function latestResult()
    {
        return $this->results()->latest('executed_at')->first();
    }
}
```

**Database Migration:**

```php
Schema::create('monitoring_checks', function (Blueprint $table) {
    $table->id();
    $table->unsignedBigInteger('monitorpy_id')->unique();
    $table->string('name');
    $table->string('plugin');
    $table->json('config');
    $table->string('status');
    $table->integer('interval')->default(300);
    $table->timestamp('last_run')->nullable();
    $table->string('last_result')->nullable();
    $table->timestamps();
});
```

### Result

Represents the result of a monitoring check execution.

**API Model Structure:**
```json
{
  "id": 1205,
  "check_id": 1,
  "status": "success",
  "message": "Website is accessible",
  "response_time": 0.523,
  "raw_data": {
    "url": "https://example.com",
    "status_code": 200,
    "expected_status": 200,
    "status_match": true
  },
  "executed_at": "2023-05-31T14:30:45Z"
}
```

**Laravel Model:**

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MonitoringResult extends Model
{
    use HasFactory;
    
    protected $fillable = [
        'monitorpy_id',
        'check_id',
        'status',
        'message',
        'response_time',
        'raw_data',
        'executed_at',
    ];
    
    protected $casts = [
        'raw_data' => 'array',
        'executed_at' => 'datetime',
        'response_time' => 'float',
    ];
    
    public function check()
    {
        return $this->belongsTo(MonitoringCheck::class, 'check_id', 'monitorpy_id');
    }
    
    public function isSuccess()
    {
        return $this->status === 'success';
    }
    
    public function isWarning()
    {
        return $this->status === 'warning';
    }
    
    public function isError()
    {
        return $this->status === 'error';
    }
}
```

**Database Migration:**

```php
Schema::create('monitoring_results', function (Blueprint $table) {
    $table->id();
    $table->unsignedBigInteger('monitorpy_id')->unique();
    $table->unsignedBigInteger('check_id');
    $table->string('status');
    $table->text('message');
    $table->float('response_time')->nullable();
    $table->json('raw_data')->nullable();
    $table->timestamp('executed_at');
    $table->timestamps();
    
    $table->index('check_id');
    $table->index(['check_id', 'executed_at']);
    $table->index(['status', 'executed_at']);
});
```

### Plugin

Represents a monitoring plugin type.

**API Model Structure:**
```json
{
  "id": "website_status",
  "name": "Website Status",
  "description": "Checks website availability and content",
  "required_config": ["url"],
  "optional_config": [
    {
      "name": "timeout",
      "type": "integer",
      "default": 30,
      "description": "Request timeout in seconds"
    }
  ]
}
```

**Laravel Model:**

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MonitoringPlugin extends Model
{
    use HasFactory;
    
    protected $fillable = [
        'plugin_id',
        'name',
        'description',
        'required_config',
        'optional_config',
    ];
    
    protected $casts = [
        'required_config' => 'array',
        'optional_config' => 'array',
    ];
    
    public function checks()
    {
        return $this->hasMany(MonitoringCheck::class, 'plugin', 'plugin_id');
    }
}
```

**Database Migration:**

```php
Schema::create('monitoring_plugins', function (Blueprint $table) {
    $table->id();
    $table->string('plugin_id')->unique();
    $table->string('name');
    $table->text('description')->nullable();
    $table->json('required_config');
    $table->json('optional_config');
    $table->timestamps();
});
```

## Model Relationships

### Check to Results

```php
// In MonitoringCheck model
public function results()
{
    return $this->hasMany(MonitoringResult::class, 'check_id', 'monitorpy_id');
}

// In MonitoringResult model
public function check()
{
    return $this->belongsTo(MonitoringCheck::class, 'check_id', 'monitorpy_id');
}
```

### Plugin to Checks

```php
// In MonitoringPlugin model
public function checks()
{
    return $this->hasMany(MonitoringCheck::class, 'plugin', 'plugin_id');
}

// In MonitoringCheck model
public function plugin()
{
    return $this->belongsTo(MonitoringPlugin::class, 'plugin', 'plugin_id');
}
```

## Syncing Data from API

To keep your Laravel models in sync with the MonitorPy API, you can create a service to periodically fetch and update data.

```php
<?php

namespace App\Services;

use App\Models\MonitoringCheck;
use App\Models\MonitoringResult;
use App\Models\MonitoringPlugin;
use Carbon\Carbon;

class MonitorPySyncService
{
    protected $monitorPy;
    
    public function __construct(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    public function syncPlugins()
    {
        $response = $this->monitorPy->request('get', '/plugins');
        $plugins = $response['data']['plugins'] ?? [];
        
        foreach ($plugins as $plugin) {
            MonitoringPlugin::updateOrCreate(
                ['plugin_id' => $plugin['id']],
                [
                    'name' => $plugin['name'],
                    'description' => $plugin['description'],
                    'required_config' => $plugin['required_config'],
                    'optional_config' => $plugin['optional_config'] ?? [],
                ]
            );
        }
        
        return count($plugins);
    }
    
    public function syncChecks()
    {
        $response = $this->monitorPy->request('get', '/checks');
        $checks = $response['data']['checks'] ?? [];
        
        foreach ($checks as $check) {
            MonitoringCheck::updateOrCreate(
                ['monitorpy_id' => $check['id']],
                [
                    'name' => $check['name'],
                    'plugin' => $check['plugin'],
                    'config' => $check['config'],
                    'status' => $check['status'],
                    'interval' => $check['interval'] ?? 300,
                    'last_run' => isset($check['last_run']) ? Carbon::parse($check['last_run']) : null,
                    'last_result' => $check['last_result'] ?? null,
                ]
            );
        }
        
        return count($checks);
    }
    
    public function syncResults($limit = 100)
    {
        $response = $this->monitorPy->request('get', '/results', ['per_page' => $limit]);
        $results = $response['data']['results'] ?? [];
        
        foreach ($results as $result) {
            MonitoringResult::updateOrCreate(
                ['monitorpy_id' => $result['id']],
                [
                    'check_id' => $result['check_id'],
                    'status' => $result['status'],
                    'message' => $result['message'],
                    'response_time' => $result['response_time'],
                    'raw_data' => $result['raw_data'] ?? null,
                    'executed_at' => Carbon::parse($result['executed_at']),
                ]
            );
        }
        
        return count($results);
    }
    
    public function syncAll()
    {
        $pluginCount = $this->syncPlugins();
        $checkCount = $this->syncChecks();
        $resultCount = $this->syncResults();
        
        return [
            'plugins' => $pluginCount,
            'checks' => $checkCount,
            'results' => $resultCount,
        ];
    }
}
```

Set up a scheduled task to run the sync operation:

```php
// In App\Console\Kernel.php
protected function schedule(Schedule $schedule)
{
    $schedule->call(function () {
        $syncService = app(MonitorPySyncService::class);
        $syncService->syncAll();
    })->hourly();
}
```

## Data Transformation

When building a Laravel application that uses MonitorPy data, you might want to transform the API data structures for your frontend. Laravel's API Resources are perfect for this:

```php
<?php

namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class MonitoringCheckResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->monitorpy_id,
            'name' => $this->name,
            'plugin' => $this->plugin,
            'config' => $this->config,
            'status' => $this->status,
            'last_check_time' => $this->last_run ? $this->last_run->diffForHumans() : 'Never',
            'last_result' => $this->last_result,
            'health_status' => $this->getHealthStatus(),
            'latest_result' => new MonitoringResultResource($this->latestResult),
            'created_at' => $this->created_at->toISOString(),
            'updated_at' => $this->updated_at->toISOString(),
        ];
    }
    
    protected function getHealthStatus()
    {
        if (!$this->last_result) {
            return 'unknown';
        }
        
        return match($this->last_result) {
            'success' => 'healthy',
            'warning' => 'degraded',
            'error' => 'unhealthy',
            default => 'unknown',
        };
    }
}
```

```php
<?php

namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class MonitoringResultResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->monitorpy_id,
            'check_id' => $this->check_id,
            'status' => $this->status,
            'message' => $this->message,
            'response_time' => $this->response_time,
            'response_time_formatted' => number_format($this->response_time, 3) . 's',
            'details' => $this->formatDetails(),
            'executed_at' => $this->executed_at->toISOString(),
            'executed_at_human' => $this->executed_at->diffForHumans(),
        ];
    }
    
    protected function formatDetails()
    {
        if (!$this->raw_data) {
            return [];
        }
        
        // Format the raw data based on plugin type
        switch ($this->check->plugin) {
            case 'website_status':
                return [
                    'url' => $this->raw_data['url'] ?? null,
                    'status_code' => $this->raw_data['status_code'] ?? null,
                    'response_size' => isset($this->raw_data['response_size']) 
                        ? $this->formatBytes($this->raw_data['response_size']) 
                        : null,
                ];
                
            case 'ssl_certificate':
                return [
                    'hostname' => $this->raw_data['hostname'] ?? null,
                    'expires_in' => isset($this->raw_data['days_remaining']) 
                        ? "{$this->raw_data['days_remaining']} days" 
                        : null,
                    'issuer' => $this->raw_data['issuer'] ?? null,
                ];
                
            default:
                return $this->raw_data;
        }
    }
    
    protected function formatBytes($bytes, $precision = 2)
    {
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        
        $bytes /= pow(1024, $pow);
        
        return round($bytes, $precision) . ' ' . $units[$pow];
    }
}
```

## Extended Models

For specific monitoring types, you may want to create specialized models:

### Website Monitoring

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class WebsiteMonitoring extends Model
{
    protected $table = 'monitoring_checks';
    
    public function scopeWebsites($query)
    {
        return $query->where('plugin', 'website_status');
    }
    
    public function getResponseTimeAttribute()
    {
        $result = $this->latestResult();
        return $result ? $result->response_time : null;
    }
    
    public function getStatusCodeAttribute()
    {
        $result = $this->latestResult();
        return $result && isset($result->raw_data['status_code']) 
            ? $result->raw_data['status_code'] 
            : null;
    }
    
    public function getUptimePercentageAttribute()
    {
        $results = $this->results()
            ->where('executed_at', '>=', now()->subDays(7))
            ->get();
            
        if ($results->isEmpty()) {
            return null;
        }
        
        $successCount = $results->where('status', 'success')->count();
        return round(($successCount / $results->count()) * 100, 2);
    }
}
```

### SSL Certificate Monitoring

```php
<?php

namespace App\Models;

use Carbon\Carbon;
use Illuminate\Database\Eloquent\Model;

class SSLMonitoring extends Model
{
    protected $table = 'monitoring_checks';
    
    public function scopeSSLCertificates($query)
    {
        return $query->where('plugin', 'ssl_certificate');
    }
    
    public function getExpirationDateAttribute()
    {
        $result = $this->latestResult();
        if (!$result || !isset($result->raw_data['valid_until'])) {
            return null;
        }
        
        return Carbon::parse($result->raw_data['valid_until']);
    }
    
    public function getDaysRemainingAttribute()
    {
        $expirationDate = $this->getExpirationDateAttribute();
        if (!$expirationDate) {
            return null;
        }
        
        return max(0, $expirationDate->diffInDays(now()));
    }
    
    public function getIsExpiredAttribute()
    {
        $expirationDate = $this->getExpirationDateAttribute();
        return $expirationDate ? $expirationDate->isPast() : null;
    }
    
    public function getIssuerAttribute()
    {
        $result = $this->latestResult();
        return $result && isset($result->raw_data['issuer']) 
            ? $result->raw_data['issuer'] 
            : null;
    }
}
```

## Read-Only vs. Read-Write Models

When integrating with MonitorPy, you have two options:

1. **Read-Only Integration**: Keep a local copy of data for display and reporting only
2. **Read-Write Integration**: Use Laravel as a frontend to create and manage MonitorPy configurations

For Read-Write integration, add methods to your models that update the API:

```php
<?php

namespace App\Models;

use App\Services\MonitorPyService;
use Illuminate\Database\Eloquent\Model;

class MonitoringCheck extends Model
{
    // ... other properties and methods
    
    public function saveToApi()
    {
        $monitorPy = app(MonitorPyService::class);
        
        $data = [
            'name' => $this->name,
            'plugin' => $this->plugin,
            'config' => $this->config,
            'status' => $this->status,
            'interval' => $this->interval,
        ];
        
        if ($this->monitorpy_id) {
            // Update existing check
            $response = $monitorPy->request('put', "/checks/{$this->monitorpy_id}", $data);
        } else {
            // Create new check
            $response = $monitorPy->request('post', '/checks', $data);
            
            // Store the ID from the API
            if (isset($response['data']['id'])) {
                $this->monitorpy_id = $response['data']['id'];
                $this->save();
            }
        }
        
        return $response;
    }
    
    public function deleteFromApi()
    {
        if (!$this->monitorpy_id) {
            return null;
        }
        
        $monitorPy = app(MonitorPyService::class);
        return $monitorPy->request('delete', "/checks/{$this->monitorpy_id}");
    }
    
    public function runCheckNow()
    {
        if (!$this->monitorpy_id) {
            return null;
        }
        
        $monitorPy = app(MonitorPyService::class);
        return $monitorPy->request('post', "/checks/{$this->monitorpy_id}/run");
    }
}
```