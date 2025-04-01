// API Base URL - Update this to match your API endpoint
let API_BASE_URL = 'http://localhost:5000/api/v1';

// Enable auto-detection of API URL based on the window location
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // If not localhost, use relative URL (assumes API is on same host)
    API_BASE_URL = '/api/v1';
}

// Global variables
let availablePlugins = [];
let checks = [];
let results = [];

// DOM elements
const apiStatus = document.getElementById('api-status');
const pluginList = document.getElementById('plugin-list');
const checksBody = document.getElementById('checks-body');
const resultsBody = document.getElementById('results-body');
const btnRefresh = document.getElementById('btn-refresh');
const btnAddCheck = document.getElementById('btn-add-check');
const addCheckModal = document.getElementById('add-check-modal');
const runCheckModal = document.getElementById('run-check-modal');
const addCheckForm = document.getElementById('add-check-form');
const checkTypeSelect = document.getElementById('check-type');
const dynamicConfig = document.getElementById('dynamic-config');

// -------------------------
// API Functions
// -------------------------

// Check API health
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok && data.status === 'healthy') {
            apiStatus.textContent = 'Connected';
            apiStatus.style.color = '#4caf50';
            return true;
        } else {
            apiStatus.textContent = 'Unhealthy';
            apiStatus.style.color = '#f44336';
            return false;
        }
    } catch (error) {
        apiStatus.textContent = 'Disconnected';
        apiStatus.style.color = '#f44336';
        console.error('API health check error:', error);
        return false;
    }
}

// Get available plugins
async function fetchPlugins() {
    try {
        const response = await fetch(`${API_BASE_URL}/plugins`);
        if (!response.ok) throw new Error('Failed to fetch plugins');
        
        const data = await response.json();
        availablePlugins = data.plugins;
        
        // Update UI
        updatePluginList();
        updatePluginDropdown();
        return availablePlugins;
    } catch (error) {
        console.error('Error fetching plugins:', error);
        return [];
    }
}

// Get all configured checks
async function fetchChecks() {
    try {
        const response = await fetch(`${API_BASE_URL}/checks`);
        if (!response.ok) throw new Error('Failed to fetch checks');
        
        const data = await response.json();
        checks = data.checks;
        
        // Update UI
        updateChecksTable();
        return checks;
    } catch (error) {
        console.error('Error fetching checks:', error);
        return [];
    }
}

// Get recent results
async function fetchResults() {
    try {
        const response = await fetch(`${API_BASE_URL}/results?per_page=10`);
        if (!response.ok) throw new Error('Failed to fetch results');
        
        const data = await response.json();
        results = data.results;
        
        // Update UI
        updateResultsTable();
        return results;
    } catch (error) {
        console.error('Error fetching results:', error);
        return [];
    }
}

// Create a new check
async function createCheck(checkData) {
    try {
        const response = await fetch(`${API_BASE_URL}/checks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(checkData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create check');
        }
        
        const data = await response.json();
        await refreshData();
        return data;
    } catch (error) {
        console.error('Error creating check:', error);
        alert(`Error creating check: ${error.message}`);
        return null;
    }
}

// Run a check
async function runCheck(checkId) {
    try {
        const response = await fetch(`${API_BASE_URL}/checks/${checkId}/run`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to run check');
        }
        
        const data = await response.json();
        await fetchResults(); // Refresh results
        return data;
    } catch (error) {
        console.error('Error running check:', error);
        alert(`Error running check: ${error.message}`);
        return null;
    }
}

// Delete a check
async function deleteCheck(checkId) {
    if (!confirm('Are you sure you want to delete this check?')) {
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/checks/${checkId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete check');
        }
        
        await refreshData();
        return true;
    } catch (error) {
        console.error('Error deleting check:', error);
        alert(`Error deleting check: ${error.message}`);
        return false;
    }
}

// -------------------------
// UI Update Functions
// -------------------------

// Update plugin list in sidebar
function updatePluginList() {
    pluginList.innerHTML = '';
    
    if (availablePlugins.length === 0) {
        pluginList.innerHTML = '<li>No plugins available</li>';
        return;
    }
    
    availablePlugins.forEach(plugin => {
        const li = document.createElement('li');
        li.textContent = plugin.name;
        pluginList.appendChild(li);
    });
}

// Update plugin dropdown in add check form
function updatePluginDropdown() {
    // Clear existing options except the first one
    while (checkTypeSelect.options.length > 1) {
        checkTypeSelect.remove(1);
    }
    
    // Add plugin options
    availablePlugins.forEach(plugin => {
        const option = document.createElement('option');
        option.value = plugin.name;
        option.textContent = plugin.name;
        checkTypeSelect.appendChild(option);
    });
}

// Update checks table
function updateChecksTable() {
    checksBody.innerHTML = '';
    
    if (checks.length === 0) {
        checksBody.innerHTML = '<tr><td colspan="5" class="center">No checks configured</td></tr>';
        return;
    }
    
    checks.forEach(check => {
        const tr = document.createElement('tr');
        
        // Get the latest result for this check (if any)
        const latestResult = results.find(r => r.check_id === check.id);
        const status = latestResult ? latestResult.status : 'unknown';
        
        tr.innerHTML = `
            <td>${check.name}</td>
            <td>${check.plugin_type}</td>
            <td class="status-${status}">${status}</td>
            <td>${check.last_run ? new Date(check.last_run).toLocaleString() : 'Never'}</td>
            <td>
                <button class="btn btn-run" data-id="${check.id}">Run</button>
                <button class="btn btn-delete" data-id="${check.id}">Delete</button>
            </td>
        `;
        
        // Add event listeners to buttons
        const runButton = tr.querySelector('.btn-run');
        runButton.addEventListener('click', () => handleRunCheck(check.id));
        
        const deleteButton = tr.querySelector('.btn-delete');
        deleteButton.addEventListener('click', () => deleteCheck(check.id));
        
        checksBody.appendChild(tr);
    });
}

// Update results table
function updateResultsTable() {
    resultsBody.innerHTML = '';
    
    if (results.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="5" class="center">No results available</td></tr>';
        return;
    }
    
    results.forEach(result => {
        // Find the check name from the check id
        const check = checks.find(c => c.id === result.check_id) || { name: 'Unknown' };
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${check.name}</td>
            <td class="status-${result.status}">${result.status}</td>
            <td>${result.response_time.toFixed(3)}s</td>
            <td>${result.message}</td>
            <td>${new Date(result.executed_at).toLocaleString()}</td>
        `;
        
        resultsBody.appendChild(tr);
    });
}

// Show result modal
function showResultModal(result) {
    // Update modal content
    document.getElementById('result-status-value').textContent = result.status;
    document.getElementById('result-status-value').className = `status-${result.status}`;
    document.getElementById('result-message-value').textContent = result.message;
    document.getElementById('result-time-value').textContent = result.response_time.toFixed(3);
    document.getElementById('result-raw-value').textContent = JSON.stringify(result.raw_data, null, 2);
    
    // Show modal
    runCheckModal.style.display = 'block';
}

// Update dynamic form fields based on selected plugin
function updateDynamicConfigFields() {
    const selectedPlugin = checkTypeSelect.value;
    dynamicConfig.innerHTML = '';
    
    if (!selectedPlugin) return;
    
    // Find the selected plugin
    const plugin = availablePlugins.find(p => p.name === selectedPlugin);
    if (!plugin) return;
    
    // Add required config fields
    if (plugin.required_config && plugin.required_config.length > 0) {
        const requiredFieldset = document.createElement('fieldset');
        requiredFieldset.innerHTML = '<legend>Required Configuration</legend>';
        
        plugin.required_config.forEach(fieldName => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';
            
            formGroup.innerHTML = `
                <label for="config-${fieldName}">${fieldName}:</label>
                <input type="text" id="config-${fieldName}" name="${fieldName}" required>
            `;
            
            requiredFieldset.appendChild(formGroup);
        });
        
        dynamicConfig.appendChild(requiredFieldset);
    }
    
    // Add optional config fields
    if (plugin.optional_config && plugin.optional_config.length > 0) {
        const optionalFieldset = document.createElement('fieldset');
        optionalFieldset.innerHTML = '<legend>Optional Configuration</legend>';
        
        plugin.optional_config.forEach(fieldName => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';
            
            formGroup.innerHTML = `
                <label for="config-${fieldName}">${fieldName}:</label>
                <input type="text" id="config-${fieldName}" name="${fieldName}">
            `;
            
            optionalFieldset.appendChild(formGroup);
        });
        
        dynamicConfig.appendChild(optionalFieldset);
    }
}

// -------------------------
// Event Handlers
// -------------------------

// Refresh all data
async function refreshData() {
    await fetchPlugins();
    await fetchChecks();
    await fetchResults();
}

// Handle add check form submission
async function handleAddCheckSubmit(event) {
    event.preventDefault();
    
    const name = document.getElementById('check-name').value;
    const pluginType = checkTypeSelect.value;
    
    if (!name || !pluginType) {
        alert('Please fill out all required fields');
        return;
    }
    
    // Get the selected plugin
    const plugin = availablePlugins.find(p => p.name === pluginType);
    if (!plugin) return;
    
    // Build config object from form
    const config = {};
    
    // Add required config fields
    if (plugin.required_config) {
        plugin.required_config.forEach(fieldName => {
            const field = document.getElementById(`config-${fieldName}`);
            if (field) config[fieldName] = field.value;
        });
    }
    
    // Add optional config fields if they have values
    if (plugin.optional_config) {
        plugin.optional_config.forEach(fieldName => {
            const field = document.getElementById(`config-${fieldName}`);
            if (field && field.value) config[fieldName] = field.value;
        });
    }
    
    // Create the check
    const checkData = {
        name,
        plugin_type: pluginType,
        config,
        enabled: true
    };
    
    const result = await createCheck(checkData);
    if (result) {
        addCheckModal.style.display = 'none';
        addCheckForm.reset();
        dynamicConfig.innerHTML = '';
    }
}

// Handle run check button
async function handleRunCheck(checkId) {
    const result = await runCheck(checkId);
    if (result) {
        showResultModal(result);
    }
}

// -------------------------
// Event Listeners
// -------------------------

// Add check button
btnAddCheck.addEventListener('click', () => {
    addCheckModal.style.display = 'block';
});

// Refresh button
btnRefresh.addEventListener('click', refreshData);

// Form submission
addCheckForm.addEventListener('submit', handleAddCheckSubmit);

// Plugin type selection changes
checkTypeSelect.addEventListener('change', updateDynamicConfigFields);

// Close buttons for modals
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
        addCheckModal.style.display = 'none';
        runCheckModal.style.display = 'none';
    });
});

// Close modals when clicking outside
window.addEventListener('click', event => {
    if (event.target === addCheckModal) {
        addCheckModal.style.display = 'none';
    }
    if (event.target === runCheckModal) {
        runCheckModal.style.display = 'none';
    }
});

// -------------------------
// Initialize the application
// -------------------------

async function init() {
    const apiHealthy = await checkApiHealth();
    if (apiHealthy) {
        await refreshData();
    } else {
        pluginList.innerHTML = '<li>API not connected</li>';
        checksBody.innerHTML = '<tr><td colspan="5" class="center">API not connected</td></tr>';
        resultsBody.innerHTML = '<tr><td colspan="5" class="center">API not connected</td></tr>';
    }
}

// Start the application
init();