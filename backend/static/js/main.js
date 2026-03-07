// State
let uploadedFiles = [];
let availablePermanentFiles = [];  // Files from file manager
let userRole = window.currentUserRole || 'employee';
let defaultClassification = window.defaultClassification || 'public_company';

// DOM
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const tempUploadBtn = document.getElementById('tempUploadBtn');
const fileInfo = document.getElementById('fileInfo');
const fileCount = document.getElementById('fileCount');
const fileList = document.getElementById('fileList');

const chatThread = document.getElementById('chatThread');
const chatPrompt = document.getElementById('chatPrompt');
const loadingSection = document.getElementById('loadingSection');
const chatAskBtn = document.getElementById('chatAskBtn');

const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const assetContainer = document.getElementById('assetContainer');
const toast = document.getElementById('toast');
const studioGenerateBtn = document.getElementById('studioGenerateBtn');
const assetType = document.getElementById('assetType');
const studioDepartment = document.getElementById('studioDepartment');
const studioPrompt = document.getElementById('studioPrompt');
const workspaceGrid = document.querySelector('.workspace-grid');
const resizerLeft = document.getElementById('resizerLeft');
const resizerRight = document.getElementById('resizerRight');

// Load available permanent files on page load
async function fetchAvailablePermanentFiles() {
    try {
        const response = await fetch('/api/user-files');
        if (response.ok) {
            const data = await response.json();
            availablePermanentFiles = data.files || [];
            uploadedFiles = (data.temporary_files || []).map((item) => ({
                file_id: item.file_id,
                name: item.filename,
                size: item.size || 0,
                ai_title: item.ai_title || item.ai_summary || item.filename || '—',
            }));
            updateLoadedFilesUI();  // Refresh UI to show available files
        }
    } catch (error) {
        console.warn('Could not fetch available files:', error);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchAvailablePermanentFiles();
});

// Upload interactions
fileInput.addEventListener('change', handleFileSelect);
tempUploadBtn.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-active');
});

uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-active');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-active');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files);
    }
});

function normalizeSelectedFiles(selectedFiles) {
    if (!selectedFiles) {
        return fileInput.files;
    }

    // Input change event
    if (selectedFiles.target && selectedFiles.target.files) {
        return selectedFiles.target.files;
    }

    // Drag/drop FileList
    if (typeof selectedFiles.length === 'number') {
        return selectedFiles;
    }

    return fileInput.files;
}

async function handleFileSelect(selectedFiles = null) {
    const files = normalizeSelectedFiles(selectedFiles);
    if (!files || files.length === 0) {
        return;
    }

    const uploadQueue = Array.from(files);
    for (const file of uploadQueue) {
        appendBubble(`Temporary document added: ${file.name}`, 'assistant');
        await uploadFile(file);
    }

    // Allow re-selecting same files repeatedly.
    fileInput.value = '';
    updateLoadedFilesUI();
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const classification = defaultClassification;

    try {
        const response = await fetch(`/api/upload?classification=${encodeURIComponent(classification)}&temporary=true`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        uploadedFiles.push({
            file_id: data.file_id,
            name: file.name,
            size: file.size,
            ai_title: data.ai_title || file.name,
        });
        updateLoadedFilesUI();
        showNotification('Temporary document uploaded.', 'success');
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed. ' + (error.message || 'Please try again.'), 'error');
    }
}

function updateLoadedFilesUI() {
    if (!fileInfo || !fileCount || !fileList) return;

    const tempCount = uploadedFiles.length;
    const permCount = availablePermanentFiles.length;
    const totalCount = tempCount + permCount;

    if (totalCount === 0) {
        fileInfo.classList.add('hidden');
        fileCount.textContent = '0';
        fileList.innerHTML = '';
        return;
    }

    fileInfo.classList.remove('hidden');
    fileCount.textContent = String(totalCount);
    
    let html = '';

    // Company managed files (permanent)
    html += '<li style="font-weight: 600; color: #7eb3dc; margin-bottom: 8px;">Company Managed Files (' + permCount + ')</li>';
    if (permCount > 0) {
        html += availablePermanentFiles
            .map(
                (item) => {
                    const aiTitle = item.ai_title || item.ai_summary || '—';
                    return `
                        <li class="doc-item-row" style="padding-left: 8px; margin-bottom: 4px;">
                            <button type="button" class="doc-open-btn" data-file-id="${item.file_id}" title="Open file" style="all: unset; cursor: pointer; color: #bbb; font-size: 13px;">
                                ${aiTitle}
                            </button>
                        </li>
                    `;
                }
            )
            .join('');
    } else {
        html += '<li style="padding-left: 8px; color: #777; font-size: 12px; margin-bottom: 8px;">No company managed files.</li>';
    }

    // Temporary files
    html += '<li style="font-weight: 600; color: #fe742e; margin-top: 10px; margin-bottom: 8px;">Temporary Files (' + tempCount + ')</li>';
    if (tempCount > 0) {
        html += uploadedFiles
            .map(
                (item) => {
                    const aiTitle = item.ai_title || item.name || '—';
                    return `
                        <li class="doc-item-row" style="padding-left: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px;">
                            <button type="button" class="doc-open-btn" data-file-id="${item.file_id}" title="Open file" style="all: unset; cursor: pointer; color: #ddd; flex: 1;">
                                ${aiTitle}
                            </button>
                            <button type="button" class="temp-delete-btn" data-file-id="${item.file_id}" title="Remove temporary file" style="border: none; background: transparent; color: #ff8a8a; font-size: 14px; cursor: pointer;">x</button>
                        </li>
                    `;
                }
            )
            .join('');
    } else {
        html += '<li style="padding-left: 8px; color: #777; font-size: 12px;">No temporary files.</li>';
    }
    
    fileList.innerHTML = html;
}

if (fileList) {
    fileList.addEventListener('click', async (event) => {
        const deleteBtn = event.target.closest('.temp-delete-btn');
        if (deleteBtn) {
            event.preventDefault();
            const fileId = deleteBtn.getAttribute('data-file-id');
            if (fileId) {
                await deleteTemporaryFile(fileId);
            }
            return;
        }

        const openBtn = event.target.closest('.doc-open-btn');
        if (openBtn) {
            event.preventDefault();
            const fileId = openBtn.getAttribute('data-file-id');
            if (fileId) {
                window.open(`/api/file/${encodeURIComponent(fileId)}/open`, '_blank', 'noopener');
            }
        }
    });
}

async function deleteTemporaryFile(fileId) {
    try {
        const response = await fetch(`/api/file/${encodeURIComponent(fileId)}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Delete failed');
        }

        uploadedFiles = uploadedFiles.filter((f) => f.file_id !== fileId);
        updateLoadedFilesUI();
        showNotification('Temporary file removed.', 'success');
    } catch (error) {
        console.error('Delete error:', error);
        showNotification(error.message || 'Could not remove temporary file.', 'error');
    }
}

// Chat interactions
chatAskBtn.addEventListener('click', async () => {
    const question = chatPrompt.value.trim();
    if (!question) {
        showNotification('Type a question in chat first.', 'error');
        return;
    }

    const selectedDepts = Array.from(document.querySelectorAll('input[name="department"]:checked')).map(
        (cb) => cb.value
    );

    appendBubble(question, 'user');

    loadingSection.classList.remove('hidden');
    chatAskBtn.disabled = true;

    try {
        // Combine temporary and permanent file IDs
        const tempFileIds = uploadedFiles.map((f) => f.file_id);
        const permFileIds = availablePermanentFiles.map((f) => f.file_id);
        const allFileIds = [...tempFileIds, ...permFileIds];
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_ids: allFileIds,
                question,
                departments: selectedDepts,
            }),
        });

        if (!response.ok) {
            let errorMessage = 'Chat failed';
            try {
                const err = await response.json();
                errorMessage = err.detail || errorMessage;
            } catch (_) {
                // Keep default when response is not JSON.
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        appendBubble(data.answer || 'No response available.', 'assistant');
        chatPrompt.value = '';
    } catch (error) {
        console.error('Chat error:', error);
        appendBubble(`Chat error: ${error.message}`, 'assistant');
        showNotification(error.message || 'Chat failed. Please try again.', 'error');
    } finally {
        loadingSection.classList.add('hidden');
        chatAskBtn.disabled = false;
    }
});

studioGenerateBtn.addEventListener('click', async () => {
    if (uploadedFiles.length === 0) {
        showNotification('Upload a temporary document before generating Studio assets.', 'error');
        return;
    }

    const latestFileId = uploadedFiles[uploadedFiles.length - 1].file_id;

    studioGenerateBtn.disabled = true;

    try {
        const response = await fetch('/api/studio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_id: latestFileId,
                asset_type: assetType.value,
                department: studioDepartment.value || null,
                custom_prompt: studioPrompt.value.trim(),
            }),
        });

        if (!response.ok) {
            let errorMessage = 'Studio generation failed';
            try {
                const err = await response.json();
                errorMessage = err.detail || errorMessage;
            } catch (_) {
                // Keep default when backend response is not JSON.
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        addStudioAssetCard(data);
        showNotification('Studio asset generated.', 'success');
    } catch (error) {
        console.error('Studio error:', error);
        showNotification(error.message || 'Studio generation failed.', 'error');
    } finally {
        studioGenerateBtn.disabled = false;
    }
});

function addStudioAssetCard(asset) {
    const hasEmpty = assetContainer.querySelector('.empty-state');
    if (hasEmpty) {
        assetContainer.innerHTML = '';
    }

    const card = document.createElement('article');
    card.className = 'asset-card';
    card.innerHTML = `
        <h3>${asset.title}</h3>
        <div class="asset-meta">${asset.asset_type.replace(/_/g, ' ')} · ${new Date(asset.timestamp).toLocaleString()}</div>
        <div class="asset-content">${asset.content}</div>
    `;

    assetContainer.prepend(card);
}

function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'report-card';

    const deptIcons = {
        engineering: '⚙️',
        sales: '📈',
        marketing: '📢',
        hr: '👥',
        operations: '🔧',
        executive: '💼',
    };

    const icon = deptIcons[report.department] || '📊';
    const deptName = report.department.charAt(0).toUpperCase() + report.department.slice(1);

    card.innerHTML = `
        <h3>${icon} ${deptName} Report</h3>
        <div class="report-section">
            <h4>Executive Summary</h4>
            <p>${report.summary}</p>
        </div>
        ${
            report.key_insights && report.key_insights.length > 0
                ? `
        <div class="report-section">
            <h4>Key Insights</h4>
            <ul>${report.key_insights.map((insight) => `<li>${insight}</li>`).join('')}</ul>
        </div>`
                : ''
        }
        ${
            report.metrics && Object.keys(report.metrics).length > 0
                ? `
        <div class="report-section">
            <h4>Key Metrics</h4>
            <div class="metrics-grid">
                ${Object.entries(report.metrics)
                    .map(
                        ([key, value]) => `
                    <div class="metric-item">
                        <span class="metric-label">${formatMetricLabel(key)}</span>
                        <span class="metric-value">${value}</span>
                    </div>`
                    )
                    .join('')}
            </div>
        </div>`
                : ''
        }
        ${
            report.recommendations && report.recommendations.length > 0
                ? `
        <div class="report-section">
            <h4>Recommendations</h4>
            <ul>${report.recommendations.map((rec) => `<li>${rec}</li>`).join('')}</ul>
        </div>`
                : ''
        }
    `;

    return card;
}

newAnalysisBtn.addEventListener('click', () => {
    uploadedFiles = [];
    fileInput.value = '';
    updateLoadedFilesUI();
    chatPrompt.value = '';
    studioPrompt.value = '';
    document.querySelectorAll('input[name="department"]').forEach((cb) => {
        cb.checked = ['engineering', 'sales', 'marketing'].includes(cb.value);
    });

    assetContainer.innerHTML = '<div class="empty-state">No asset yet. Use Studio controls above to generate one.</div>';
    appendBubble('Workspace reset. You can ask general questions or upload temporary docs anytime.', 'assistant');
    showNotification('Workspace reset complete.', 'success');
});

function appendBubble(text, role = 'assistant') {
    const bubble = document.createElement('div');
    bubble.className = `bubble bubble-${role}`;
    bubble.textContent = text;
    chatThread.appendChild(bubble);
    chatThread.scrollTop = chatThread.scrollHeight;
}

function formatFileSize(bytes) {
    if (bytes === 0) {
        return '0 Bytes';
    }
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatMetricLabel(key) {
    return key
        .replace(/_/g, ' ')
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function showNotification(message, type = 'info') {
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.style.borderLeftColor = type === 'error' ? '#ff4d4f' : 'var(--accent)';

    clearTimeout(showNotification.timeout);
    showNotification.timeout = setTimeout(() => {
        toast.classList.add('hidden');
    }, 3200);
}

function initResizablePanels() {
    if (!workspaceGrid || !resizerLeft || !resizerRight) {
        return;
    }

    const MIN_LEFT = 240;
    const MIN_CENTER = 420;
    const MIN_RIGHT = 290;
    const HANDLE_WIDTH = 10;
    const GAP = 16;

    let leftWidth = 300;
    let rightWidth = 360;

    function applyGridColumns() {
        if (window.innerWidth <= 1120) {
            workspaceGrid.style.gridTemplateColumns = '1fr';
            return;
        }

        workspaceGrid.style.gridTemplateColumns = `${leftWidth}px ${HANDLE_WIDTH}px minmax(${MIN_CENTER}px, 1fr) ${HANDLE_WIDTH}px ${rightWidth}px`;
    }

    function getAvailableWidth() {
        const styles = window.getComputedStyle(workspaceGrid);
        const horizontalPadding =
            parseFloat(styles.paddingLeft || '0') + parseFloat(styles.paddingRight || '0');
        return workspaceGrid.clientWidth - horizontalPadding;
    }

    function startDragging(side, event) {
        if (window.innerWidth <= 1120) {
            return;
        }

        event.preventDefault();
        const startX = event.clientX;
        const startLeft = leftWidth;
        const startRight = rightWidth;
        const totalWidth = getAvailableWidth();
        const reserved = (2 * HANDLE_WIDTH) + (4 * GAP) + MIN_CENTER;

        const activeHandle = side === 'left' ? resizerLeft : resizerRight;
        activeHandle.classList.add('active');

        function onMouseMove(moveEvent) {
            const deltaX = moveEvent.clientX - startX;

            if (side === 'left') {
                let proposedLeft = startLeft + deltaX;
                const maxLeft = totalWidth - reserved - rightWidth;
                proposedLeft = Math.max(MIN_LEFT, Math.min(maxLeft, proposedLeft));
                leftWidth = proposedLeft;
            } else {
                let proposedRight = startRight - deltaX;
                const maxRight = totalWidth - reserved - leftWidth;
                proposedRight = Math.max(MIN_RIGHT, Math.min(maxRight, proposedRight));
                rightWidth = proposedRight;
            }

            applyGridColumns();
        }

        function onMouseUp() {
            activeHandle.classList.remove('active');
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    }

    resizerLeft.addEventListener('mousedown', (event) => startDragging('left', event));
    resizerRight.addEventListener('mousedown', (event) => startDragging('right', event));

    window.addEventListener('resize', applyGridColumns);
    applyGridColumns();
}

initResizablePanels();
