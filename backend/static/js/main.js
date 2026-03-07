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
const studioAssetIcons = document.getElementById('studioAssetIcons');
const studioConfigModal = document.getElementById('studioConfigModal');
const studioConfigTitle = document.getElementById('studioConfigTitle');
const studioConfigCloseBtn = document.getElementById('studioConfigCloseBtn');
const studioConfigCancelBtn = document.getElementById('studioConfigCancelBtn');
const studioConfigGenerateBtn = document.getElementById('studioConfigGenerateBtn');
const studioModalDepartment = document.getElementById('studioModalDepartment');
const studioModalPrompt = document.getElementById('studioModalPrompt');
const studioModalComplexity = document.getElementById('studioModalComplexity');
const studioModalLength = document.getElementById('studioModalLength');
const studioAssetViewModal = document.getElementById('studioAssetViewModal');
const studioAssetViewTitle = document.getElementById('studioAssetViewTitle');
const studioAssetViewMeta = document.getElementById('studioAssetViewMeta');
const studioAssetViewContent = document.getElementById('studioAssetViewContent');
const studioAssetViewCitations = document.getElementById('studioAssetViewCitations');
const studioAssetViewCloseBtn = document.getElementById('studioAssetViewCloseBtn');
const studioAssetCloseBtn = document.getElementById('studioAssetCloseBtn');
const studioAssetDeleteBtn = document.getElementById('studioAssetDeleteBtn');
const studioAssetShareBtn = document.getElementById('studioAssetShareBtn');
const workspaceGrid = document.querySelector('.workspace-grid');
const resizerLeft = document.getElementById('resizerLeft');
const resizerRight = document.getElementById('resizerRight');

let selectedStudioAssetType = null;
let selectedStudioAssetLabel = null;
let generatedStudioAssets = [];
let selectedGeneratedAssetId = null;

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
        appendBubble(data.answer || 'No response available.', 'assistant', data.citations || []);
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

if (studioAssetIcons) {
    studioAssetIcons.addEventListener('click', (event) => {
        const button = event.target.closest('.studio-icon-btn');
        if (!button) {
            return;
        }

        if (uploadedFiles.length === 0) {
            showNotification('Upload a temporary document before generating Studio assets.', 'error');
            return;
        }

        selectedStudioAssetType = button.getAttribute('data-asset-type');
        selectedStudioAssetLabel = button.getAttribute('data-asset-label') || 'Studio Asset';

        studioConfigTitle.textContent = `Generate ${selectedStudioAssetLabel}`;
        studioConfigModal.style.display = 'block';
        studioConfigModal.setAttribute('aria-hidden', 'false');
    });
}

function closeStudioConfigModal() {
    if (!studioConfigModal) {
        return;
    }
    studioConfigModal.style.display = 'none';
    studioConfigModal.setAttribute('aria-hidden', 'true');
}

if (studioConfigCloseBtn) {
    studioConfigCloseBtn.addEventListener('click', closeStudioConfigModal);
}
if (studioConfigCancelBtn) {
    studioConfigCancelBtn.addEventListener('click', closeStudioConfigModal);
}
if (studioConfigModal) {
    studioConfigModal.addEventListener('click', (event) => {
        if (event.target === studioConfigModal) {
            closeStudioConfigModal();
        }
    });
}

if (studioConfigGenerateBtn) {
    studioConfigGenerateBtn.addEventListener('click', async () => {
        if (!selectedStudioAssetType) {
            showNotification('Choose an asset type first.', 'error');
            return;
        }
        if (uploadedFiles.length === 0) {
            showNotification('Upload a temporary document before generating Studio assets.', 'error');
            return;
        }

        const latestFileId = uploadedFiles[uploadedFiles.length - 1].file_id;
        const pendingCardId = addPendingStudioAssetCard(selectedStudioAssetLabel || 'Generated Asset');
        studioConfigGenerateBtn.disabled = true;

        try {
            const response = await fetch('/api/studio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_id: latestFileId,
                    asset_type: selectedStudioAssetType,
                    department: studioModalDepartment.value || null,
                    custom_prompt: studioModalPrompt.value.trim(),
                    complexity: studioModalComplexity.value,
                    length: studioModalLength.value,
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
            removePendingStudioAssetCard(pendingCardId);
            addStudioAssetCard(data);
            closeStudioConfigModal();
            showNotification('Studio asset generated.', 'success');
        } catch (error) {
            removePendingStudioAssetCard(pendingCardId);
            console.error('Studio error:', error);
            showNotification(error.message || 'Studio generation failed.', 'error');
        } finally {
            studioConfigGenerateBtn.disabled = false;
        }
    });
}

function addPendingStudioAssetCard(assetLabel) {
    const hasEmpty = assetContainer.querySelector('.empty-state');
    if (hasEmpty) {
        assetContainer.innerHTML = '';
    }

    const pendingId = `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const card = document.createElement('article');
    card.className = 'asset-card asset-card-pending';
    card.setAttribute('data-pending-asset-id', pendingId);
    card.innerHTML = `
        <h3>${assetLabel}</h3>
        <div class="asset-meta">${new Date().toLocaleString()}</div>
        <div class="asset-loading-row">
            <span class="asset-spinner" aria-hidden="true"></span>
            <span>Generating...</span>
        </div>
    `;

    assetContainer.prepend(card);
    return pendingId;
}

function removePendingStudioAssetCard(pendingId) {
    const pendingCard = assetContainer.querySelector(`[data-pending-asset-id="${pendingId}"]`);
    if (pendingCard) {
        pendingCard.remove();
    }

    if (!assetContainer.querySelector('.asset-card') && !assetContainer.querySelector('.empty-state')) {
        assetContainer.innerHTML = '<div class="empty-state">No asset yet. Use Studio controls above to generate one.</div>';
    }
}

function addStudioAssetCard(asset) {
    const hasEmpty = assetContainer.querySelector('.empty-state');
    if (hasEmpty) {
        assetContainer.innerHTML = '';
    }

    const generatedAsset = {
        ...asset,
        _id: `asset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    };
    generatedStudioAssets.unshift(generatedAsset);

    const card = document.createElement('article');
    card.className = 'asset-card';
    card.setAttribute('data-generated-asset-id', generatedAsset._id);
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    const imagePreview = generatedAsset.image_data_url
        ? `<img class="asset-card-thumb" src="${generatedAsset.image_data_url}" alt="${generatedAsset.title}" />`
        : '';

    card.innerHTML = `
        <h3>${generatedAsset.title}</h3>
        <div class="asset-meta">${new Date(generatedAsset.timestamp).toLocaleString()}</div>
        ${imagePreview}
    `;

    assetContainer.prepend(card);
}

if (assetContainer) {
    assetContainer.addEventListener('click', (event) => {
        const card = event.target.closest('.asset-card');
        if (!card) {
            return;
        }
        const generatedAssetId = card.getAttribute('data-generated-asset-id');
        if (generatedAssetId) {
            openGeneratedAssetModal(generatedAssetId);
        }
    });

    assetContainer.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        const card = event.target.closest('.asset-card');
        if (!card) {
            return;
        }
        event.preventDefault();
        const generatedAssetId = card.getAttribute('data-generated-asset-id');
        if (generatedAssetId) {
            openGeneratedAssetModal(generatedAssetId);
        }
    });
}

function openGeneratedAssetModal(assetId) {
    const asset = generatedStudioAssets.find((item) => item._id === assetId);
    if (!asset || !studioAssetViewModal) {
        return;
    }

    selectedGeneratedAssetId = assetId;
    studioAssetViewTitle.textContent = asset.title || 'Generated Asset';
    studioAssetViewMeta.textContent = `${asset.asset_type.replace(/_/g, ' ')} · ${new Date(asset.timestamp).toLocaleString()}`;
    if (asset.image_data_url) {
        const captionHtml = asset.content ? `<div class="asset-image-caption">${parseMarkdown(asset.content)}</div>` : '';
        studioAssetViewContent.innerHTML = `
            <div class="asset-view-image-wrap">
                <img src="${asset.image_data_url}" alt="${asset.title || 'Generated infographic'}" class="asset-view-image" />
            </div>
            ${captionHtml}
        `;
        if (studioAssetShareBtn) {
            studioAssetShareBtn.textContent = 'Download';
        }
    } else {
        studioAssetViewContent.innerHTML = parseMarkdown(asset.content || '');
        if (studioAssetShareBtn) {
            studioAssetShareBtn.textContent = 'Share';
        }
    }

    // Render citations if present
    if (asset.citations && asset.citations.length > 0) {
        studioAssetViewCitations.classList.remove('hidden');
        studioAssetViewCitations.innerHTML = `
            <div class="citations-label">Sources</div>
            <div class="citations-list">
                ${asset.citations
                    .map(
                        (citation, index) =>
                            `<button type="button" class="citation-badge" data-asset-citation-index="${index}">[${citation.citation_id}] ${citation.filename}</button>`
                    )
                    .join('')}
            </div>
        `;
    } else {
        studioAssetViewCitations.classList.add('hidden');
        studioAssetViewCitations.innerHTML = '';
    }

    studioAssetViewModal.style.display = 'block';
    studioAssetViewModal.setAttribute('aria-hidden', 'false');
}

function closeGeneratedAssetModal() {
    if (!studioAssetViewModal) {
        return;
    }
    studioAssetViewModal.style.display = 'none';
    studioAssetViewModal.setAttribute('aria-hidden', 'true');
    selectedGeneratedAssetId = null;
}

if (studioAssetViewModal) {
    studioAssetViewModal.addEventListener('click', (event) => {
        if (event.target === studioAssetViewModal) {
            closeGeneratedAssetModal();
            return;
        }

        const citationButton = event.target.closest('[data-asset-citation-index]');
        if (!citationButton || !selectedGeneratedAssetId) {
            return;
        }
        const index = Number(citationButton.getAttribute('data-asset-citation-index'));
        const asset = generatedStudioAssets.find((item) => item._id === selectedGeneratedAssetId);
        if (asset && asset.citations && asset.citations[index]) {
            showCitationModal(asset.citations[index]);
        }
    });
}

if (studioAssetViewCloseBtn) {
    studioAssetViewCloseBtn.addEventListener('click', closeGeneratedAssetModal);
}
if (studioAssetCloseBtn) {
    studioAssetCloseBtn.addEventListener('click', closeGeneratedAssetModal);
}
if (studioAssetDeleteBtn) {
    studioAssetDeleteBtn.addEventListener('click', () => {
        if (!selectedGeneratedAssetId) {
            return;
        }
        generatedStudioAssets = generatedStudioAssets.filter((item) => item._id !== selectedGeneratedAssetId);
        const card = assetContainer.querySelector(`[data-generated-asset-id="${selectedGeneratedAssetId}"]`);
        if (card) {
            card.remove();
        }
        if (!assetContainer.querySelector('.asset-card')) {
            assetContainer.innerHTML = '<div class="empty-state">No asset yet. Use Studio controls above to generate one.</div>';
        }
        closeGeneratedAssetModal();
        showNotification('Generated asset deleted.', 'success');
    });
}
if (studioAssetShareBtn) {
    studioAssetShareBtn.addEventListener('click', () => {
        const asset = selectedGeneratedAssetId
            ? generatedStudioAssets.find((item) => item._id === selectedGeneratedAssetId)
            : null;

        if (asset && asset.image_data_url) {
            const link = document.createElement('a');
            link.href = asset.image_data_url;
            link.download = `${(asset.title || 'infographic').replace(/\s+/g, '_').toLowerCase()}.svg`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            showNotification('Infographic downloaded.', 'success');
            return;
        }

        showNotification('Share will be enabled soon.', 'info');
    });
}

function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'report-card';

    const deptIcons = {
        engineering: '<span class="material-symbols-outlined">settings</span>',
        sales: '<span class="material-symbols-outlined">trending_up</span>',
        marketing: '<span class="material-symbols-outlined">campaign</span>',
        hr: '<span class="material-symbols-outlined">group</span>',
        operations: '<span class="material-symbols-outlined">build</span>',
        executive: '<span class="material-symbols-outlined">business_center</span>',
    };

    const icon = deptIcons[report.department] || '<span class="material-symbols-outlined">bar_chart</span>';
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
    if (studioModalPrompt) {
        studioModalPrompt.value = '';
    }
    document.querySelectorAll('input[name="department"]').forEach((cb) => {
        cb.checked = ['engineering', 'sales', 'marketing'].includes(cb.value);
    });

    assetContainer.innerHTML = '<div class="empty-state">No asset yet. Use Studio controls above to generate one.</div>';
    generatedStudioAssets = [];
    closeGeneratedAssetModal();
    appendBubble('Workspace reset. You can ask general questions or upload temporary docs anytime.', 'assistant');
    showNotification('Workspace reset complete.', 'success');
});

function parseMarkdown(text) {
    const escapeHtml = (value) => value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    const applyInlineMarkdown = (value) => {
        let html = value;
        // Code spans first so other markdown does not alter code content.
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
        html = html.replace(/\*([^\s*][^*]*?)\*/g, '<em>$1</em>');
        html = html.replace(/\b_([^\s_][^_]*?)_\b/g, '<em>$1</em>');
        return html;
    };

    const lines = text.split('\n');
    const blocks = [];
    let i = 0;

    while (i < lines.length) {
        const rawLine = lines[i] || '';
        const trimmed = rawLine.trim();

        // Skip blank lines between blocks.
        if (!trimmed) {
            i += 1;
            continue;
        }

        // Fenced code block
        if (trimmed.startsWith('```')) {
            const codeLines = [];
            i += 1;
            while (i < lines.length && !lines[i].trim().startsWith('```')) {
                codeLines.push(lines[i]);
                i += 1;
            }
            if (i < lines.length) {
                i += 1; // consume closing ```
            }
            blocks.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
            continue;
        }

        // Unordered list: *, -, or bullet symbol prefix.
        if (/^(\*|-|•)\s+/.test(trimmed)) {
            const items = [];
            while (i < lines.length && /^(\*|-|•)\s+/.test((lines[i] || '').trim())) {
                const itemText = (lines[i] || '').trim().replace(/^(\*|-|•)\s+/, '');
                items.push(`<li>${applyInlineMarkdown(escapeHtml(itemText))}</li>`);
                i += 1;
            }
            blocks.push(`<ul>${items.join('')}</ul>`);
            continue;
        }

        // Ordered list: 1. 2. etc.
        if (/^\d+\.\s+/.test(trimmed)) {
            const items = [];
            while (i < lines.length && /^\d+\.\s+/.test((lines[i] || '').trim())) {
                const itemText = (lines[i] || '').trim().replace(/^\d+\.\s+/, '');
                items.push(`<li>${applyInlineMarkdown(escapeHtml(itemText))}</li>`);
                i += 1;
            }
            blocks.push(`<ol>${items.join('')}</ol>`);
            continue;
        }

        // Paragraph block (collect until blank line or list/code start).
        const paragraphLines = [];
        while (i < lines.length) {
            const line = lines[i] || '';
            const nextTrimmed = line.trim();
            if (!nextTrimmed) {
                break;
            }
            if (nextTrimmed.startsWith('```') || /^(\*|-|•)\s+/.test(nextTrimmed) || /^\d+\.\s+/.test(nextTrimmed)) {
                break;
            }
            paragraphLines.push(escapeHtml(line));
            i += 1;
        }
        const paragraph = applyInlineMarkdown(paragraphLines.join('<br>'));
        blocks.push(`<p>${paragraph}</p>`);
    }

    return blocks.join('');
}

function appendBubble(text, role = 'assistant', citations = []) {
    const bubble = document.createElement('div');
    bubble.className = `bubble bubble-${role}`;
    
    // Parse markdown and render as HTML
    const formattedText = parseMarkdown(text);
    bubble.innerHTML = formattedText;
    
    // Add citations if present
    if (citations && citations.length > 0) {
        const citationsContainer = document.createElement('div');
        citationsContainer.className = 'citations-container';
        citationsContainer.innerHTML = '<div class="citations-label">Sources:</div>';
        
        const citationsList = document.createElement('div');
        citationsList.className = 'citations-list';
        
        citations.forEach(citation => {
            const citationBtn = document.createElement('button');
            citationBtn.className = 'citation-badge';
            citationBtn.textContent = `[${citation.citation_id}] ${citation.filename}`;
            citationBtn.title = citation.text_preview;
            citationBtn.onclick = () => showCitationModal(citation);
            citationsList.appendChild(citationBtn);
        });
        
        citationsContainer.appendChild(citationsList);
        bubble.appendChild(citationsContainer);
    }
    
    chatThread.appendChild(bubble);
    chatThread.scrollTop = chatThread.scrollHeight;
}

// Show citation modal with excerpt
function showCitationModal(citation) {
    // Create modal if not exists
    let modal = document.getElementById('citationModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'citationModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content citation-modal">
                <div class="modal-header">
                    <h3>Source Citation</h3>
                    <button class="modal-close" onclick="document.getElementById('citationModal').style.display='none'">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="citation-info">
                        <p><strong>File:</strong> <span id="citationFilename"></span></p>
                        <p><strong>Relevance:</strong> <span id="citationRelevance"></span></p>
                    </div>
                    <div class="citation-excerpt">
                        <h4>Excerpt:</h4>
                        <pre id="citationText"></pre>
                    </div>
                    <div class="citation-actions">
                        <button class="btn-secondary" onclick="openFullDocument(document.getElementById('citationModal').dataset.fileId)">View Full Document</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close on outside click
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
    
    // Populate modal with citation data
    document.getElementById('citationFilename').textContent = citation.filename;
    document.getElementById('citationRelevance').textContent = `${(citation.relevance_score * 100).toFixed(1)}%`;
    document.getElementById('citationText').textContent = citation.text_preview;
    modal.dataset.fileId = citation.file_id;
    
    modal.style.display = 'block';
}

// Open full document in new tab
function openFullDocument(fileId) {
    window.open(`/api/file/${fileId}/open`, '_blank');
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
