console.log('🚀 CUSTOM CHECK UPDATES JS LOADED');

// Try multiple times to find and attach to the button
function attachToButton() {
    console.log('Attempting to attach to check updates button...');
    
    const checkBtn = document.getElementById('check-updates-btn');
    if (checkBtn) {
        console.log('Check button found, adding click handler');
        
        // Remove any existing listeners first
        checkBtn.removeEventListener('click', checkForUpdates);
        
        // Add our click handler
        checkBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Check button clicked');
            checkForUpdates();
        });
        
        console.log('✅ Click handler attached successfully');
        return true;
    } else {
        console.log('Check button not found, retrying...');
        return false;
    }
}

// Try immediately when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, setting up check updates button');
        
        // Try immediately
        if (!attachToButton()) {
            // If not found, try again after a delay
            setTimeout(attachToButton, 100);
            setTimeout(attachToButton, 500);
            setTimeout(attachToButton, 1000);
        }
    });
} else {
    console.log('DOM already loaded, setting up check updates button immediately');
    
    // Try immediately
    if (!attachToButton()) {
        // If not found, try again after a delay
        setTimeout(attachToButton, 100);
        setTimeout(attachToButton, 500);
        setTimeout(attachToButton, 1000);
    }
}

function checkForUpdates() {
    console.log('checkForUpdates called');
    const button = document.getElementById('check-updates-btn');
    const originalText = button.textContent;
    
    button.textContent = '🔍 Checking...';
    button.disabled = true;
    
    showStatusMessage('Checking GitHub for updates...', 'info');
    
    // Get CSRF token from Django admin
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    
    console.log('CSRF token:', csrfToken);
    console.log('Making AJAX request to:', '/updates/ajax/check/');
    
    fetch('/updates/ajax/check/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        button.textContent = originalText;
        button.disabled = false;
        
        if (data.success) {
            if (data.update_available) {
                showStatusMessage(
                    `✅ Update available: ${data.latest_version}! ${data.critical ? '(CRITICAL UPDATE)' : ''}`, 
                    'success'
                );
                // Refresh the page after 3 seconds to show new updates
                setTimeout(() => window.location.reload(), 3000);
            } else {
                showStatusMessage('✅ You are running the latest version!', 'success');
            }
        } else {
            showStatusMessage(`❌ Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        button.textContent = originalText;
        button.disabled = false;
        showStatusMessage('❌ Network error checking for updates', 'error');
    });
}

function showStatusMessage(message, type) {
    console.log('showStatusMessage called:', message, type);
    
    // Create status div if it doesn't exist
    let statusDiv = document.getElementById('update-status-message');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'update-status-message';
        statusDiv.style.cssText = 'display: none; padding: 10px; margin: 15px 0; border-radius: 4px; border: 1px solid #ccc;';
        
        // Try to find a good place to insert it
        const contentStart = document.querySelector('#content-start') || 
                           document.querySelector('.module') ||
                           document.querySelector('#changelist');
        
        if (contentStart) {
            contentStart.parentNode.insertBefore(statusDiv, contentStart);
        } else {
            document.body.appendChild(statusDiv);
        }
    }
    
    const colors = {
        'success': '#d4edda',
        'error': '#f8d7da',
        'info': '#d1ecf1'
    };
    const borderColors = {
        'success': '#c3e6cb',
        'error': '#f5c6cb',
        'info': '#bee5eb'
    };
    
    statusDiv.textContent = message;
    statusDiv.style.backgroundColor = colors[type];
    statusDiv.style.borderColor = borderColors[type];
    statusDiv.style.color = '#333';
    statusDiv.style.fontWeight = 'bold';
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => statusDiv.style.display = 'none', 5000);
    }
}

// Install update function (called from action buttons)
function installUpdate(version, critical) {
    const criticalWarning = critical === 'True' ? '\n⚠️ This is a CRITICAL update.\n' : '';
    
    if (!confirm(`Install version ${version}?${criticalWarning}\nThis will:\n1. Create a backup\n2. Download and install the update\n3. Apply database migrations\n\nProceed?`)) {
        return;
    }

    showStatusMessage(`Starting installation of version ${version}...`, 'info');

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     document.cookie.match(/csrftoken=([^;]+)/)?.[1];

    fetch('/updates/ajax/install/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            version: version
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatusMessage(`✅ Update to ${version} started successfully!`, 'success');
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showStatusMessage(`❌ Installation failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showStatusMessage('❌ Network error starting installation', 'error');
    });
}