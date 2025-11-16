// Business Simulation Game - Main JavaScript

// API Helper Functions
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, message: 'Network error' };
    }
}

// Stock Trading
async function buyStock(companyId, shares) {
    const result = await apiRequest('/api/stock/buy', 'POST', {
        company_id: companyId,
        shares: shares
    });

    if (result.success) {
        showAlert('Stock purchased successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } else {
        showAlert(result.message, 'danger');
    }

    return result;
}

async function sellStock(companyId, shares) {
    const result = await apiRequest('/api/stock/sell', 'POST', {
        company_id: companyId,
        shares: shares
    });

    if (result.success) {
        showAlert('Stock sold successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } else {
        showAlert(result.message, 'danger');
    }

    return result;
}

// Capital Transfer
async function transferCapital(companyId, capitalType, amount, direction) {
    const result = await apiRequest('/api/company/' + companyId + '/capital/transfer', 'POST', {
        capital_type: capitalType,
        amount: amount,
        direction: direction
    });

    if (result.success) {
        showAlert('Capital transferred successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } else {
        showAlert(result.message, 'danger');
    }

    return result;
}

// Facility Management
async function shutdownFacility(facilityId) {
    if (!confirm('Are you sure you want to shutdown this facility?')) {
        return;
    }

    const result = await apiRequest('/api/facility/' + facilityId + '/shutdown', 'POST');

    if (result.success) {
        showAlert('Facility shut down successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } else {
        showAlert(result.message, 'danger');
    }

    return result;
}

async function activateFacility(facilityId) {
    const result = await apiRequest('/api/facility/' + facilityId + '/activate', 'POST');

    if (result.success) {
        showAlert('Facility activated successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } else {
        showAlert(result.message, 'danger');
    }

    return result;
}

// UI Helpers
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatCurrency(amount) {
    return '$' + amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatPercentage(value) {
    return (value * 100).toFixed(1) + '%';
}

// Auto-refresh for game updates (every 30 seconds)
let autoRefreshEnabled = false;

function enableAutoRefresh() {
    if (!autoRefreshEnabled) {
        autoRefreshEnabled = true;
        setInterval(() => {
            // Only refresh if user hasn't interacted recently
            if (document.hidden) {
                location.reload();
            }
        }, 30000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Business Simulation Game loaded');

    // Enable tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
