# MonitorPy Laravel Integration Examples

This document provides practical examples of integrating MonitorPy with Laravel applications.

## Basic Integration Example

This example shows a complete Laravel service class for integrating with MonitorPy.

### MonitorPy Service Class

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class MonitorPyService
{
    protected $baseUrl;
    protected $apiKey;
    protected $token;
    
    public function __construct()
    {
        $this->baseUrl = config('monitorpy.api_url');
        $this->apiKey = config('monitorpy.api_key');
        $this->token = Cache::get('monitorpy_token');
    }
    
    /**
     * Authenticate with the MonitorPy API using JWT
     */
    public function login($email = null, $password = null)
    {
        $email = $email ?? config('monitorpy.auth_email');
        $password = $password ?? config('monitorpy.auth_password');
        
        try {
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
            
            Log::error('MonitorPy authentication failed', [
                'status' => $response->status(),
                'response' => $response->json(),
            ]);
            
            return false;
        } catch (\Exception $e) {
            Log::error('MonitorPy authentication exception', [
                'message' => $e->getMessage(),
            ]);
            
            return false;
        }
    }
    
    /**
     * Make an authenticated request to the MonitorPy API
     */
    public function request($method, $endpoint, $data = [])
    {
        try {
            $client = Http::timeout(config('monitorpy.timeout', 30))
                ->acceptJson();
            
            // Add authentication
            if (config('monitorpy.auth_method', 'jwt') === 'jwt') {
                if (!$this->token && !$this->login()) {
                    throw new \Exception('Could not authenticate with MonitorPy API');
                }
                
                $client = $client->withToken($this->token);
            } else {
                $client = $client->withHeaders([
                    'X-API-Key' => $this->apiKey,
                ]);
            }
            
            $url = rtrim($this->baseUrl, '/') . '/' . ltrim($endpoint, '/');
            $response = $client->$method($url, $data);
            
            // Check for token expiration and retry once
            if ($response->status() === 401 && config('monitorpy.auth_method', 'jwt') === 'jwt') {
                Cache::forget('monitorpy_token');
                $this->token = null;
                
                if ($this->login()) {
                    $client = Http::timeout(config('monitorpy.timeout', 30))
                        ->acceptJson()
                        ->withToken($this->token);
                    
                    $response = $client->$method($url, $data);
                }
            }
            
            if ($response->failed()) {
                Log::warning('MonitorPy API request failed', [
                    'method' => $method,
                    'endpoint' => $endpoint,
                    'status' => $response->status(),
                    'response' => $response->json(),
                ]);
            }
            
            return $response->json();
        } catch (\Exception $e) {
            Log::error('MonitorPy API request exception', [
                'method' => $method,
                'endpoint' => $endpoint,
                'message' => $e->getMessage(),
            ]);
            
            return [
                'status' => 'error',
                'message' => $e->getMessage(),
                'data' => null,
            ];
        }
    }
    
    /**
     * Get all available monitoring plugins
     */
    public function getPlugins()
    {
        $response = $this->request('get', '/plugins');
        return $response['data']['plugins'] ?? [];
    }
    
    /**
     * Get all configured checks
     */
    public function getChecks($page = 1, $perPage = 20)
    {
        $response = $this->request('get', '/checks', [
            'page' => $page,
            'per_page' => $perPage,
        ]);
        
        return [
            'checks' => $response['data']['checks'] ?? [],
            'meta' => $response['meta'] ?? null,
        ];
    }
    
    /**
     * Get a specific check by ID
     */
    public function getCheck($checkId)
    {
        $response = $this->request('get', "/checks/{$checkId}");
        return $response['data'] ?? null;
    }
    
    /**
     * Create a new monitoring check
     */
    public function createCheck($name, $plugin, $config, $interval = 300, $status = 'active')
    {
        $response = $this->request('post', '/checks', [
            'name' => $name,
            'plugin' => $plugin,
            'config' => $config,
            'interval' => $interval,
            'status' => $status,
        ]);
        
        return $response['data'] ?? null;
    }
    
    /**
     * Update an existing check
     */
    public function updateCheck($checkId, $data)
    {
        $response = $this->request('put', "/checks/{$checkId}", $data);
        return $response['data'] ?? null;
    }
    
    /**
     * Delete a check
     */
    public function deleteCheck($checkId)
    {
        $response = $this->request('delete', "/checks/{$checkId}");
        return $response['status'] === 'success';
    }
    
    /**
     * Run a check immediately
     */
    public function runCheck($checkId)
    {
        $response = $this->request('post', "/checks/{$checkId}/run");
        return $response['data'] ?? null;
    }
    
    /**
     * Get check results
     */
    public function getResults($checkId = null, $page = 1, $perPage = 20)
    {
        $params = [
            'page' => $page,
            'per_page' => $perPage,
        ];
        
        if ($checkId) {
            $params['check_id'] = $checkId;
        }
        
        $response = $this->request('get', '/results', $params);
        
        return [
            'results' => $response['data']['results'] ?? [],
            'meta' => $response['meta'] ?? null,
        ];
    }
}
```

### Service Provider Registration

```php
<?php

namespace App\Providers;

use App\Services\MonitorPyService;
use Illuminate\Support\ServiceProvider;

class MonitorPyServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(MonitorPyService::class, function ($app) {
            return new MonitorPyService();
        });
        
        $this->mergeConfigFrom(
            __DIR__.'/../config/monitorpy.php', 'monitorpy'
        );
    }
    
    public function boot()
    {
        $this->publishes([
            __DIR__.'/../config/monitorpy.php' => config_path('monitorpy.php'),
        ], 'monitorpy-config');
    }
}
```

### Example Controller

```php
<?php

namespace App\Http\Controllers;

use App\Services\MonitorPyService;
use Illuminate\Http\Request;
use App\Http\Resources\MonitoringCheckResource;

class MonitoringController extends Controller
{
    protected $monitorPy;
    
    public function __construct(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    /**
     * Display a dashboard of monitoring checks
     */
    public function dashboard()
    {
        $checksData = $this->monitorPy->getChecks();
        $checks = $checksData['checks'];
        
        return view('monitoring.dashboard', [
            'checks' => $checks,
            'summary' => $this->getStatusSummary($checks),
        ]);
    }
    
    /**
     * Calculate a summary of check statuses
     */
    protected function getStatusSummary($checks)
    {
        $summary = [
            'total' => count($checks),
            'success' => 0,
            'warning' => 0,
            'error' => 0,
            'unknown' => 0,
        ];
        
        foreach ($checks as $check) {
            if (!isset($check['last_result'])) {
                $summary['unknown']++;
                continue;
            }
            
            $status = $check['last_result'];
            
            if (isset($summary[$status])) {
                $summary[$status]++;
            } else {
                $summary['unknown']++;
            }
        }
        
        return $summary;
    }
    
    /**
     * Show the form for creating a new check
     */
    public function create()
    {
        $plugins = $this->monitorPy->getPlugins();
        
        return view('monitoring.create', [
            'plugins' => $plugins,
        ]);
    }
    
    /**
     * Store a newly created check
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'plugin' => 'required|string',
            'interval' => 'nullable|integer|min:60',
        ]);
        
        // Validate plugin-specific configuration
        $config = $this->validatePluginConfig($request);
        
        $check = $this->monitorPy->createCheck(
            $validated['name'],
            $validated['plugin'],
            $config,
            $validated['interval'] ?? 300,
            'active'
        );
        
        if (!$check) {
            return back()->withErrors(['message' => 'Failed to create check'])->withInput();
        }
        
        return redirect()->route('monitoring.dashboard')
            ->with('success', 'Monitoring check created successfully');
    }
    
    /**
     * Validate plugin-specific configuration fields
     */
    protected function validatePluginConfig(Request $request)
    {
        $plugin = $request->input('plugin');
        $config = [];
        
        switch ($plugin) {
            case 'website_status':
                $request->validate([
                    'config.url' => 'required|url',
                    'config.timeout' => 'nullable|integer|min:1|max:300',
                    'config.expected_status' => 'nullable|integer|min:100|max:599',
                ]);
                
                $config = [
                    'url' => $request->input('config.url'),
                    'timeout' => $request->input('config.timeout', 30),
                    'expected_status' => $request->input('config.expected_status', 200),
                ];
                break;
                
            case 'ssl_certificate':
                $request->validate([
                    'config.hostname' => 'required|string',
                    'config.port' => 'nullable|integer|min:1|max:65535',
                    'config.warning_days' => 'nullable|integer|min:1',
                    'config.critical_days' => 'nullable|integer|min:1',
                ]);
                
                $config = [
                    'hostname' => $request->input('config.hostname'),
                    'port' => $request->input('config.port', 443),
                    'warning_days' => $request->input('config.warning_days', 30),
                    'critical_days' => $request->input('config.critical_days', 7),
                ];
                break;
                
            case 'mail_server':
                $request->validate([
                    'config.hostname' => 'required|string',
                    'config.protocol' => 'required|in:smtp,imap,pop3',
                    'config.port' => 'nullable|integer|min:1|max:65535',
                ]);
                
                $config = [
                    'hostname' => $request->input('config.hostname'),
                    'protocol' => $request->input('config.protocol'),
                    'port' => $request->input('config.port'),
                    'timeout' => $request->input('config.timeout', 30),
                ];
                break;
                
            // Other plugin configurations...
        }
        
        return $config;
    }
    
    /**
     * Show a specific check details
     */
    public function show($id)
    {
        $check = $this->monitorPy->getCheck($id);
        
        if (!$check) {
            abort(404, 'Check not found');
        }
        
        // Get recent results
        $resultsData = $this->monitorPy->getResults($id, 1, 10);
        $results = $resultsData['results'];
        
        return view('monitoring.show', [
            'check' => $check,
            'results' => $results,
        ]);
    }
    
    /**
     * Show the form for editing a check
     */
    public function edit($id)
    {
        $check = $this->monitorPy->getCheck($id);
        
        if (!$check) {
            abort(404, 'Check not found');
        }
        
        $plugins = $this->monitorPy->getPlugins();
        
        return view('monitoring.edit', [
            'check' => $check,
            'plugins' => $plugins,
        ]);
    }
    
    /**
     * Update the specified check
     */
    public function update(Request $request, $id)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'interval' => 'nullable|integer|min:60',
            'status' => 'nullable|in:active,paused',
        ]);
        
        // Update only the configuration fields that were provided
        $config = [];
        foreach ($request->input('config', []) as $key => $value) {
            if ($value !== null && $value !== '') {
                $config[$key] = $value;
            }
        }
        
        $data = [
            'name' => $validated['name'],
        ];
        
        if (!empty($validated['interval'])) {
            $data['interval'] = $validated['interval'];
        }
        
        if (!empty($validated['status'])) {
            $data['status'] = $validated['status'];
        }
        
        if (!empty($config)) {
            $data['config'] = $config;
        }
        
        $check = $this->monitorPy->updateCheck($id, $data);
        
        if (!$check) {
            return back()->withErrors(['message' => 'Failed to update check'])->withInput();
        }
        
        return redirect()->route('monitoring.show', $id)
            ->with('success', 'Monitoring check updated successfully');
    }
    
    /**
     * Remove the specified check
     */
    public function destroy($id)
    {
        $success = $this->monitorPy->deleteCheck($id);
        
        if (!$success) {
            return back()->withErrors(['message' => 'Failed to delete check']);
        }
        
        return redirect()->route('monitoring.dashboard')
            ->with('success', 'Monitoring check deleted successfully');
    }
    
    /**
     * Run a check immediately
     */
    public function run($id)
    {
        $result = $this->monitorPy->runCheck($id);
        
        if (!$result) {
            return back()->withErrors(['message' => 'Failed to run check']);
        }
        
        return redirect()->route('monitoring.show', $id)
            ->with('success', 'Check executed successfully');
    }
    
    /**
     * API endpoint for getting checks (JSON)
     */
    public function apiChecks()
    {
        $checksData = $this->monitorPy->getChecks();
        $checks = $checksData['checks'];
        
        return response()->json([
            'checks' => $checks,
            'summary' => $this->getStatusSummary($checks),
        ]);
    }
}
```

## Dashboard Example

### Creating a Monitoring Dashboard in Laravel

```php
<?php

namespace App\Http\Controllers;

use App\Services\MonitorPyService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

class DashboardController extends Controller
{
    protected $monitorPy;
    
    public function __construct(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    public function index()
    {
        // Cache the dashboard data for 1 minute to reduce API calls
        $dashboardData = Cache::remember('monitorpy_dashboard', 60, function () {
            return $this->getDashboardData();
        });
        
        return view('dashboard', $dashboardData);
    }
    
    protected function getDashboardData()
    {
        // Get all checks
        $checksData = $this->monitorPy->getChecks(1, 100);
        $checks = $checksData['checks'] ?? [];
        
        // Group checks by type
        $groupedChecks = [
            'website' => [],
            'ssl' => [],
            'mail' => [],
            'dns' => [],
            'other' => [],
        ];
        
        foreach ($checks as $check) {
            $type = $this->getCheckType($check['plugin']);
            $groupedChecks[$type][] = $check;
        }
        
        // Calculate status summary
        $summary = [
            'total' => count($checks),
            'healthy' => 0,
            'warning' => 0,
            'error' => 0,
            'unknown' => 0,
        ];
        
        foreach ($checks as $check) {
            $status = $check['last_result'] ?? 'unknown';
            
            switch ($status) {
                case 'success':
                    $summary['healthy']++;
                    break;
                case 'warning':
                    $summary['warning']++;
                    break;
                case 'error':
                    $summary['error']++;
                    break;
                default:
                    $summary['unknown']++;
                    break;
            }
        }
        
        // Get recent results
        $recentResults = [];
        if (!empty($checks)) {
            $resultsData = $this->monitorPy->getResults(null, 1, 10);
            $recentResults = $resultsData['results'] ?? [];
        }
        
        return [
            'checks' => $checks,
            'groupedChecks' => $groupedChecks,
            'summary' => $summary,
            'recentResults' => $recentResults,
        ];
    }
    
    protected function getCheckType($plugin)
    {
        switch ($plugin) {
            case 'website_status':
                return 'website';
            case 'ssl_certificate':
                return 'ssl';
            case 'mail_server':
                return 'mail';
            case 'dns':
                return 'dns';
            default:
                return 'other';
        }
    }
}
```

### Dashboard View

```html
<!-- resources/views/dashboard.blade.php -->
@extends('layouts.app')

@section('content')
<div class="container">
    <h1 class="mb-4">Monitoring Dashboard</h1>
    
    <!-- Status Summary -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-white bg-success">
                <div class="card-body">
                    <h5 class="card-title">Healthy</h5>
                    <p class="card-text display-4">{{ $summary['healthy'] }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-warning">
                <div class="card-body">
                    <h5 class="card-title">Warning</h5>
                    <p class="card-text display-4">{{ $summary['warning'] }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-danger">
                <div class="card-body">
                    <h5 class="card-title">Error</h5>
                    <p class="card-text display-4">{{ $summary['error'] }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-secondary">
                <div class="card-body">
                    <h5 class="card-title">Unknown</h5>
                    <p class="card-text display-4">{{ $summary['unknown'] }}</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Website Checks -->
    @if(count($groupedChecks['website']) > 0)
    <div class="card mb-4">
        <div class="card-header">
            <h4>Website Monitoring</h4>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>URL</th>
                            <th>Last Check</th>
                            <th>Status</th>
                            <th>Response Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($groupedChecks['website'] as $check)
                        <tr>
                            <td>{{ $check['name'] }}</td>
                            <td>{{ $check['config']['url'] ?? 'N/A' }}</td>
                            <td>{{ \Carbon\Carbon::parse($check['last_run'])->diffForHumans() }}</td>
                            <td>
                                @if($check['last_result'] == 'success')
                                    <span class="badge bg-success">Success</span>
                                @elseif($check['last_result'] == 'warning')
                                    <span class="badge bg-warning">Warning</span>
                                @elseif($check['last_result'] == 'error')
                                    <span class="badge bg-danger">Error</span>
                                @else
                                    <span class="badge bg-secondary">Unknown</span>
                                @endif
                            </td>
                            <td>
                                @if(isset($check['last_result_data']['response_time']))
                                    {{ number_format($check['last_result_data']['response_time'], 3) }}s
                                @else
                                    N/A
                                @endif
                            </td>
                            <td>
                                <a href="{{ route('monitoring.show', $check['id']) }}" class="btn btn-sm btn-primary">
                                    View
                                </a>
                                <form method="POST" action="{{ route('monitoring.run', $check['id']) }}" class="d-inline">
                                    @csrf
                                    <button type="submit" class="btn btn-sm btn-secondary">
                                        Run Now
                                    </button>
                                </form>
                            </td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    @endif
    
    <!-- SSL Certificate Checks -->
    @if(count($groupedChecks['ssl']) > 0)
    <div class="card mb-4">
        <div class="card-header">
            <h4>SSL Certificate Monitoring</h4>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Hostname</th>
                            <th>Expires In</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($groupedChecks['ssl'] as $check)
                        <tr>
                            <td>{{ $check['name'] }}</td>
                            <td>{{ $check['config']['hostname'] ?? 'N/A' }}</td>
                            <td>
                                @if(isset($check['last_result_data']['days_remaining']))
                                    {{ $check['last_result_data']['days_remaining'] }} days
                                @else
                                    N/A
                                @endif
                            </td>
                            <td>
                                @if($check['last_result'] == 'success')
                                    <span class="badge bg-success">Valid</span>
                                @elseif($check['last_result'] == 'warning')
                                    <span class="badge bg-warning">Expiring Soon</span>
                                @elseif($check['last_result'] == 'error')
                                    <span class="badge bg-danger">Invalid/Expired</span>
                                @else
                                    <span class="badge bg-secondary">Unknown</span>
                                @endif
                            </td>
                            <td>
                                <a href="{{ route('monitoring.show', $check['id']) }}" class="btn btn-sm btn-primary">
                                    View
                                </a>
                                <form method="POST" action="{{ route('monitoring.run', $check['id']) }}" class="d-inline">
                                    @csrf
                                    <button type="submit" class="btn btn-sm btn-secondary">
                                        Run Now
                                    </button>
                                </form>
                            </td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    @endif
    
    <!-- Recent Results -->
    <div class="card">
        <div class="card-header">
            <h4>Recent Check Results</h4>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Check</th>
                            <th>Status</th>
                            <th>Message</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($recentResults as $result)
                        <tr>
                            <td>{{ $result['check_name'] ?? 'Unknown' }}</td>
                            <td>
                                @if($result['status'] == 'success')
                                    <span class="badge bg-success">Success</span>
                                @elseif($result['status'] == 'warning')
                                    <span class="badge bg-warning">Warning</span>
                                @elseif($result['status'] == 'error')
                                    <span class="badge bg-danger">Error</span>
                                @else
                                    <span class="badge bg-secondary">Unknown</span>
                                @endif
                            </td>
                            <td>{{ $result['message'] }}</td>
                            <td>{{ \Carbon\Carbon::parse($result['executed_at'])->diffForHumans() }}</td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
@endsection
```

## Notifications Example

### Creating Monitoring Notifications

```php
<?php

namespace App\Notifications;

use Illuminate\Notifications\Notification;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Messages\SlackMessage;

class MonitoringAlert extends Notification
{
    protected $result;
    
    public function __construct($result)
    {
        $this->result = $result;
    }
    
    public function via($notifiable)
    {
        return ['mail', 'slack', 'database'];
    }
    
    public function toMail($notifiable)
    {
        $subject = "[MonitorPy] {$this->result['status']} - {$this->result['check_name']}";
        
        $mail = (new MailMessage)
            ->subject($subject)
            ->line("A monitoring alert has been triggered:");
            
        // Add status badge
        if ($this->result['status'] === 'error') {
            $mail->error("Status: Error");
        } elseif ($this->result['status'] === 'warning') {
            $mail->warning("Status: Warning");
        } else {
            $mail->success("Status: {$this->result['status']}");
        }
        
        $mail->line("Check: {$this->result['check_name']}")
            ->line("Message: {$this->result['message']}")
            ->line("Time: {$this->result['executed_at']}");
        
        // Add check-specific details
        if (isset($this->result['raw_data'])) {
            $details = $this->getDetailsForEmail();
            foreach ($details as $label => $value) {
                $mail->line("{$label}: {$value}");
            }
        }
        
        $mail->action('View Details', url("/monitoring/results/{$this->result['id']}"));
        
        return $mail;
    }
    
    public function toSlack($notifiable)
    {
        $statusEmoji = $this->getStatusEmoji();
        
        return (new SlackMessage)
            ->from('MonitorPy', ':chart_with_upwards_trend:')
            ->to('#monitoring')
            ->content("Monitoring Alert: {$statusEmoji} *{$this->result['status']}* for *{$this->result['check_name']}*")
            ->attachment(function ($attachment) {
                $attachment->title('Details')
                    ->content($this->result['message'])
                    ->fields([
                        'Time' => $this->result['executed_at'],
                        'Status' => $this->result['status'],
                    ])
                    ->color($this->getStatusColor());
                
                // Add check-specific details
                $details = $this->getDetailsForSlack();
                foreach ($details as $label => $value) {
                    $attachment->field($label, $value);
                }
            });
    }
    
    public function toDatabase($notifiable)
    {
        return [
            'check_id' => $this->result['check_id'],
            'check_name' => $this->result['check_name'],
            'status' => $this->result['status'],
            'message' => $this->result['message'],
            'executed_at' => $this->result['executed_at'],
        ];
    }
    
    protected function getStatusColor()
    {
        return match ($this->result['status']) {
            'success' => 'good',
            'warning' => 'warning',
            'error' => 'danger',
            default => '#CCCCCC',
        };
    }
    
    protected function getStatusEmoji()
    {
        return match ($this->result['status']) {
            'success' => ':white_check_mark:',
            'warning' => ':warning:',
            'error' => ':x:',
            default => ':question:',
        };
    }
    
    protected function getDetailsForEmail()
    {
        $rawData = $this->result['raw_data'] ?? [];
        $plugin = $this->result['plugin'] ?? '';
        
        $details = [];
        
        switch ($plugin) {
            case 'website_status':
                if (isset($rawData['status_code'])) {
                    $details['Status Code'] = $rawData['status_code'];
                }
                if (isset($rawData['response_time'])) {
                    $details['Response Time'] = "{$rawData['response_time']} seconds";
                }
                break;
                
            case 'ssl_certificate':
                if (isset($rawData['days_remaining'])) {
                    $details['Days Remaining'] = $rawData['days_remaining'];
                }
                if (isset($rawData['issuer'])) {
                    $details['Issuer'] = $rawData['issuer'];
                }
                break;
                
            // Other plugins...
        }
        
        return $details;
    }
    
    protected function getDetailsForSlack()
    {
        // Similar to getDetailsForEmail() but formatted for Slack
        return $this->getDetailsForEmail();
    }
}
```

### Creating a Webhook Handler

```php
<?php

namespace App\Http\Controllers;

use App\Events\MonitoringCheckUpdated;
use App\Models\MonitoringCheck;
use App\Models\MonitoringResult;
use App\Notifications\MonitoringAlert;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Notification;

class WebhookController extends Controller
{
    /**
     * Handle an incoming webhook from MonitorPy
     */
    public function handleMonitoringWebhook(Request $request)
    {
        $payload = $request->all();
        
        Log::debug('Received MonitorPy webhook', [
            'event' => $payload['event'] ?? 'unknown',
        ]);
        
        switch ($payload['event'] ?? '') {
            case 'check.result':
                return $this->handleCheckResult($payload['data'] ?? []);
                
            case 'check.created':
                return $this->handleCheckCreated($payload['data'] ?? []);
                
            case 'check.updated':
                return $this->handleCheckUpdated($payload['data'] ?? []);
                
            case 'check.deleted':
                return $this->handleCheckDeleted($payload['data'] ?? []);
                
            default:
                return response()->json([
                    'status' => 'error',
                    'message' => 'Unknown event type',
                ], 400);
        }
    }
    
    /**
     * Handle a check result webhook
     */
    protected function handleCheckResult($data)
    {
        // Store the result
        $result = MonitoringResult::create([
            'monitorpy_id' => $data['id'],
            'check_id' => $data['check_id'],
            'status' => $data['status'],
            'message' => $data['message'],
            'response_time' => $data['response_time'] ?? null,
            'raw_data' => $data['raw_data'] ?? null,
            'executed_at' => $data['executed_at'],
        ]);
        
        // Update the check's last_result
        $check = MonitoringCheck::where('monitorpy_id', $data['check_id'])->first();
        if ($check) {
            $check->update([
                'last_result' => $data['status'],
                'last_run' => $data['executed_at'],
            ]);
        }
        
        // Send notifications for warning/error results
        if (in_array($data['status'], ['warning', 'error'])) {
            $this->sendNotifications($result);
        }
        
        return response()->json([
            'status' => 'success',
            'message' => 'Result processed successfully',
        ]);
    }
    
    /**
     * Send notifications about a result
     */
    protected function sendNotifications($result)
    {
        // Send to users with "monitoring" permission
        $users = \App\Models\User::whereHas('permissions', function ($query) {
            $query->where('name', 'monitoring');
        })->get();
        
        Notification::send($users, new MonitoringAlert($result));
        
        // Log the notification
        Log::info('Monitoring notification sent', [
            'check_id' => $result->check_id,
            'status' => $result->status,
            'recipients' => $users->count(),
        ]);
    }
    
    /**
     * Handle a check created webhook
     */
    protected function handleCheckCreated($data)
    {
        MonitoringCheck::create([
            'monitorpy_id' => $data['id'],
            'name' => $data['name'],
            'plugin' => $data['plugin'],
            'config' => $data['config'],
            'status' => $data['status'],
            'interval' => $data['interval'] ?? 300,
        ]);
        
        return response()->json([
            'status' => 'success',
            'message' => 'Check created successfully',
        ]);
    }
    
    /**
     * Handle a check updated webhook
     */
    protected function handleCheckUpdated($data)
    {
        $check = MonitoringCheck::where('monitorpy_id', $data['id'])->first();
        
        if ($check) {
            $check->update([
                'name' => $data['name'],
                'plugin' => $data['plugin'],
                'config' => $data['config'],
                'status' => $data['status'],
                'interval' => $data['interval'] ?? 300,
            ]);
            
            event(new MonitoringCheckUpdated($check));
        }
        
        return response()->json([
            'status' => 'success',
            'message' => 'Check updated successfully',
        ]);
    }
    
    /**
     * Handle a check deleted webhook
     */
    protected function handleCheckDeleted($data)
    {
        MonitoringCheck::where('monitorpy_id', $data['id'])->delete();
        
        return response()->json([
            'status' => 'success',
            'message' => 'Check deleted successfully',
        ]);
    }
}
```

## API Routes Example

```php
<?php

use App\Http\Controllers\MonitoringController;
use App\Http\Controllers\WebhookController;
use Illuminate\Support\Facades\Route;

// Admin routes
Route::middleware(['auth', 'admin'])->prefix('admin')->group(function () {
    Route::prefix('monitoring')->name('monitoring.')->group(function () {
        Route::get('/', [MonitoringController::class, 'dashboard'])
            ->name('dashboard');
        Route::get('/create', [MonitoringController::class, 'create'])
            ->name('create');
        Route::post('/', [MonitoringController::class, 'store'])
            ->name('store');
        Route::get('/{id}', [MonitoringController::class, 'show'])
            ->name('show');
        Route::get('/{id}/edit', [MonitoringController::class, 'edit'])
            ->name('edit');
        Route::put('/{id}', [MonitoringController::class, 'update'])
            ->name('update');
        Route::delete('/{id}', [MonitoringController::class, 'destroy'])
            ->name('destroy');
        Route::post('/{id}/run', [MonitoringController::class, 'run'])
            ->name('run');
    });
});

// API routes
Route::prefix('api')->group(function () {
    // Public API endpoints
    Route::get('/monitoring/status', [MonitoringController::class, 'publicStatus']);
    
    // Protected API endpoints
    Route::middleware(['auth:api'])->group(function () {
        Route::get('/monitoring/checks', [MonitoringController::class, 'apiChecks']);
        Route::get('/monitoring/results', [MonitoringController::class, 'apiResults']);
    });
    
    // Webhook endpoints
    Route::post('/webhooks/monitorpy', [WebhookController::class, 'handleMonitoringWebhook'])
        ->middleware('webhook.signature');
});
```

## Livewire Component Example

```php
<?php

namespace App\Http\Livewire;

use App\Services\MonitorPyService;
use Livewire\Component;
use Livewire\WithPagination;

class MonitoringDashboard extends Component
{
    use WithPagination;
    
    public $filter = 'all';
    public $search = '';
    public $refreshInterval = 30000; // 30 seconds
    
    protected $monitorPy;
    
    public function boot(MonitorPyService $monitorPy)
    {
        $this->monitorPy = $monitorPy;
    }
    
    public function render()
    {
        $checksData = $this->getChecks();
        
        return view('livewire.monitoring-dashboard', [
            'checks' => $checksData['checks'],
            'summary' => $this->getStatusSummary($checksData['checks']),
        ]);
    }
    
    public function getChecks()
    {
        $params = [
            'page' => $this->page,
            'per_page' => 10,
        ];
        
        // Apply status filter
        if ($this->filter !== 'all') {
            $params['status'] = $this->filter;
        }
        
        // Apply search filter (if MonitorPy API supports it)
        if (!empty($this->search)) {
            $params['search'] = $this->search;
        }
        
        return $this->monitorPy->getChecks($params['page'], $params['per_page']);
    }
    
    protected function getStatusSummary($checks)
    {
        $summary = [
            'total' => count($checks),
            'success' => 0,
            'warning' => 0,
            'error' => 0,
            'unknown' => 0,
        ];
        
        foreach ($checks as $check) {
            $status = $check['last_result'] ?? 'unknown';
            
            if (isset($summary[$status])) {
                $summary[$status]++;
            } else {
                $summary['unknown']++;
            }
        }
        
        return $summary;
    }
    
    public function runCheck($id)
    {
        $result = $this->monitorPy->runCheck($id);
        
        if ($result) {
            session()->flash('message', 'Check executed successfully');
        } else {
            session()->flash('error', 'Failed to run check');
        }
    }
    
    public function toggleCheckStatus($id, $currentStatus)
    {
        $newStatus = $currentStatus === 'active' ? 'paused' : 'active';
        
        $result = $this->monitorPy->updateCheck($id, [
            'status' => $newStatus,
        ]);
        
        if ($result) {
            session()->flash('message', "Check {$newStatus}");
        } else {
            session()->flash('error', 'Failed to update check status');
        }
    }
}
```