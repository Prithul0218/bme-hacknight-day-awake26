// State
let uploadedFileId = null;
let userRole = 'employee'; // Default role

// DOM
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const tempUploadBtn = document.getElementById('tempUploadBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const userRoleSelect = document.getElementById('userRole');
const fileClassificationSelect = document.getElementById('fileClassification');

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

// Track user role changes
userRoleSelect.addEventListener('change', (e) => {
    userRole = e.target.value;
    showNotification(`Role changed to: ${userRole}`, 'success');
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
        fileInput.files = files;
        handleFileSelect();
    }
});

async function handleFileSelect() {
    const file = fileInput.files[0];
    if (!file) {
        return;
    }

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.classList.remove('hidden');
    appendBubble(`Temporary document added: ${file.name}`, 'assistant');

    await uploadFile(file);
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const classification = fileClassificationSelect.value || 'public_company';

    try {
        const response = await fetch(`/api/upload?classification=${encodeURIComponent(classification)}`, {
            method: 'POST',
            headers: {
                'X-User-Role': userRole,
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        uploadedFileId = data.file_id;
        showNotification(`Document uploaded as ${classification.replace(/_/g, ' ')} classification.`, 'success');
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed. ' + (error.message || 'Please try again.'), 'error');
    }
}

// Chat interactions
chatAskBtn.addEventListener('click', async () => {
    if (!uploadedFileId) {
        showNotification('Upload a temporary document before asking questions.', 'error');
        return;
    }

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
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': userRole,
            },
            body: JSON.stringify({
                file_id: uploadedFileId,
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
    if (!uploadedFileId) {
        showNotification('Upload a temporary document before generating Studio assets.', 'error');
        return;
    }

    studioGenerateBtn.disabled = true;

    try {
        const response = await fetch('/api/studio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-Role': userRole,
            },
            body: JSON.stringify({
                file_id: uploadedFileId,
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
    uploadedFileId = null;
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    chatPrompt.value = '';
    studioPrompt.value = '';
    fileClassificationSelect.value = 'public_company';

    document.querySelectorAll('input[name="department"]').forEach((cb) => {
        cb.checked = ['engineering', 'sales', 'marketing'].includes(cb.value);
    });

    assetContainer.innerHTML = '<div class="empty-state">No asset yet. Use Studio controls above to generate one.</div>';
    appendBubble('Workspace reset. Upload a temporary document to begin again.', 'assistant');
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
