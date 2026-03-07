/**
 * File Manager JavaScript
 * Handles file deletion with confirmation modal
 */

document.addEventListener('DOMContentLoaded', function() {
    setupFileDeleteHandlers();
});

function setupFileDeleteHandlers() {
    const deleteButtons = document.querySelectorAll('.delete-file-btn');
    const deleteModal = document.getElementById('deleteConfirmModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const deleteFileName = document.getElementById('deleteFileName');
    
    let fileIdToDelete = null;
    
    // Handle delete button clicks
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            fileIdToDelete = this.dataset.fileId;
            const row = document.querySelector(`tr[data-file-id="${fileIdToDelete}"]`);
            const filename = row.querySelector('.file-name-col span:nth-of-type(2)').textContent;
            
            deleteFileName.textContent = `Are you sure you want to delete "${filename}"?`;
            deleteModal.classList.add('show');
        });
    });
    
    // Handle cancel button
    cancelDeleteBtn.addEventListener('click', function() {
        deleteModal.classList.remove('show');
        fileIdToDelete = null;
    });
    
    // Close modal when clicking outside
    deleteModal.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            deleteModal.classList.remove('show');
            fileIdToDelete = null;
        }
    });
    
    // Handle confirm delete
    confirmDeleteBtn.addEventListener('click', async function() {
        if (!fileIdToDelete) return;
        
        try {
            const response = await fetch(`/api/file/${fileIdToDelete}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                showNotification(`Error: ${error.detail || 'Failed to delete file'}`, 'error');
            } else {
                const data = await response.json();
                showNotification('File deleted successfully', 'success');
                
                // Remove row from table
                const row = document.querySelector(`tr[data-file-id="${fileIdToDelete}"]`);
                if (row) {
                    row.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        row.remove();
                        
                        // Check if table is now empty
                        const tbody = document.getElementById('filesTableBody');
                        if (tbody && tbody.children.length === 0) {
                            location.reload(); // Reload to show empty state
                        }
                    }, 300);
                }
            }
        } catch (error) {
            console.error('Delete error:', error);
            showNotification(`Error: ${error.message}`, 'error');
        }
        
        deleteModal.classList.remove('show');
        fileIdToDelete = null;
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#2a5a2a' : type === 'error' ? '#5a2a2a' : '#2a2a5a'};
        color: ${type === 'success' ? '#7ec97e' : type === 'error' ? '#dc6e6e' : '#7eb3dc'};
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        z-index: 2000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(20px);
        }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
