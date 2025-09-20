// Updates check functionality
console.log('🚀 Updates check JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, adding check updates button');
    
    // Add check button to the page
    const toolbar = document.querySelector('.object-tools');
    if (toolbar) {
        const buttonHtml = `
            <li style="float: left; margin-right: 10px;">
                <button type="button" id="check-updates-btn" onclick="checkForUpdates()" 
                        style="background: #007cba; color: white; padding: 8px 15px; border: none; 
                               border-radius: 4px; font-weight: bold; cursor: pointer;">
                    🔍 Check for Updates Now
                </button>
            </li>
        `;
        toolbar.insertAdjacentHTML('afterbegin', buttonHtml);
        console.log('✅ Check updates button added');
    } else {
        console.log('❌ Toolbar not found');
    }
});

function checkForUpdates() {
    console.log('checkForUpdates called');
    const button = document.getElementById('check-updates-btn');
    const originalText = button.textContent;
    
    button.textContent = '🔍 Checking...';
    button.disabled = true;
    
    showMessage('Checking GitHub for updates...', 'info');
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/updates/ajax/check/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        button.textContent = originalText;
        button.disabled = false;
        
        if (data.success) {
            if (data.update_available) {
                showMessage(
                    `✅ Update available: ${data.latest_version}!\n` +
                    `Current: ${data.current_version}\n` +
                    `${data.prerelease ? '(Pre-release)' : ''}`,
                    'success'
                );
                setTimeout(() => window.location.reload(), 3000);
            } else {
                showMessage(
                    `✅ You are running the latest version!\n` +
                    `Current: ${data.current_version}`,
                    'success'
                );
            }
        } else {
            showMessage(`❌ Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        button.textContent = originalText;
        button.disabled = false;
        showMessage('❌ Network error checking for updates', 'error');
    });
}

function showMessage(message, type) {
    console.log('showMessage called:', message, type);
    
    let messageDiv = document.getElementById('update-message');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'update-message';
        messageDiv.style.cssText = 'padding: 15px; margin: 15px 0; border-radius: 4px; font-weight: bold; white-space: pre-line;';
        
        const content = document.querySelector('#changelist') || document.querySelector('.module');
        if (content && content.parentNode) {
            content.parentNode.insertBefore(messageDiv, content);
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
    
    messageDiv.textContent = message;
    messageDiv.style.backgroundColor = colors[type];
    messageDiv.style.borderColor = borderColors[type];
    messageDiv.style.color = '#333';
    messageDiv.style.border = `1px solid ${borderColors[type]}`;
    messageDiv.style.display = 'block';
    
    if (type === 'success') {
        setTimeout(() => messageDiv.style.display = 'none', 8000);
    }
}