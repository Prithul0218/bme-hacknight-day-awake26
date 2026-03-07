/**
 * Auto Reports / Alert History Page JavaScript
 * Handles acknowledgment of triggered alerts
 */

document.addEventListener('DOMContentLoaded', () => {
    initializeAcknowledgeButtons();
});

/**
 * Initialize all acknowledge buttons
 */
function initializeAcknowledgeButtons() {
    const acknowledgeButtons = document.querySelectorAll('.acknowledge-btn');
    
    acknowledgeButtons.forEach(button => {
        button.addEventListener('click', handleAcknowledge);
    });
}

/**
 * Handle acknowledge button click
 */
async function handleAcknowledge(event) {
    const button = event.currentTarget;
    const triggerId = button.dataset.triggerId;
    
    if (!triggerId) {
        console.error('No trigger ID found on button');
        return;
    }
    
    // Disable button and show loading state
    button.disabled = true;
    const originalContent = button.innerHTML;
    button.innerHTML = '<span class="material-symbols-outlined">hourglass_empty</span> Acknowledging...';
    
    try {
        const response = await fetch(`/api/triggered-alerts/${triggerId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            throw new Error(`Failed to acknowledge alert: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Update UI to show acknowledged state
        updateAcknowledgedUI(triggerId, result.trigger);
        
    } catch (error) {
        console.error('Error acknowledging alert:', error);
        
        // Restore button on error
        button.disabled = false;
        button.innerHTML = originalContent;
        
        // Show error message
        showErrorMessage(button, 'Failed to acknowledge alert. Please try again.');
    }
}

/**
 * Update the UI to show acknowledged state
 */
function updateAcknowledgedUI(triggerId, trigger) {
    const alertCard = document.querySelector(`[data-trigger-id="${triggerId}"]`);
    
    if (!alertCard) return;
    
    const actionsDiv = alertCard.querySelector('.alert-actions');
    
    if (!actionsDiv) return;
    
    // Format the timestamp
    const acknowledgedAt = formatTimestamp(trigger.acknowledged_at);
    
    // Replace button with acknowledged status
    actionsDiv.innerHTML = `
        <div class="acknowledged-status">
            <span class="material-symbols-outlined">check_circle</span>
            <span>Acknowledged by ${trigger.acknowledged_by} at ${acknowledgedAt}</span>
        </div>
    `;
}

/**
 * Format ISO timestamp to readable format
 */
function formatTimestamp(isoString) {
    if (!isoString) return 'just now';
    
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds
        
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        
        // Format as date if older than a day
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (e) {
        return isoString;
    }
}

/**
 * Show error message near button
 */
function showErrorMessage(button, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        padding: 0.5rem;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 6px;
    `;
    
    button.parentElement.appendChild(errorDiv);
    
    // Remove error message after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}
