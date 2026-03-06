// Upload Manager - Single File Upload with Access Levels

let currentFile = null;
let currentFileId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeUploadForm();
});

function initializeUploadForm() {
    const fileInput = document.getElementById('documentFile');
    const uploadArea = document.querySelector('.upload-area');
    const uploadDetails = document.querySelector('.upload-details');
    const storageModeSelect = document.getElementById('storageMode');
    const uploadBtn = document.getElementById('uploadBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const removeBtn = document.querySelector('.btn-remove');
    const regenerateBtn = document.querySelector('.btn-regenerate');
    const uploadAnotherBtn = document.getElementById('uploadAnotherBtn');
    const summaryRendered = document.getElementById('documentSummaryRendered');
    const summarySource = document.getElementById('documentSummary');

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Storage mode change
    storageModeSelect.addEventListener('change', (e) => {
        handleStorageModeChange(e.target.value);
    });

    // Upload button
    uploadBtn.addEventListener('click', handleUpload);

    // Cancel button
    cancelBtn.addEventListener('click', resetForm);

    // Remove file button
    removeBtn.addEventListener('click', resetForm);

    // Regenerate summary button
    regenerateBtn.addEventListener('click', () => generateSummary(true));

    // Upload another button
    uploadAnotherBtn.addEventListener('click', resetForm);

    // Keep hidden summary source in sync with user edits.
    summaryRendered.addEventListener('input', () => {
        summarySource.value = summaryRendered.innerText.trim();
    });
}

function handleFileSelect(file) {
    currentFile = file;

    // Show file preview
    const uploadArea = document.querySelector('.upload-area');
    const uploadDetails = document.querySelector('.upload-details');
    const fileName = document.querySelector('.file-name');
    const fileSize = document.querySelector('.file-size');
    const titleInput = document.getElementById('documentTitle');

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    // Auto-generate title
    titleInput.value = generateTitleFromFilename(file.name);

    // Show details, hide upload area
    uploadArea.classList.add('hidden');
    uploadDetails.classList.remove('hidden');
}

function handleStorageModeChange(mode) {
    const summarySection = document.querySelector('.summary-section');

    if (mode === 'summary') {
        summarySection.classList.remove('hidden');
        generateSummary();
    } else {
        summarySection.classList.add('hidden');
    }
}

async function generateSummary(regenerate = false) {
    const summaryText = document.getElementById('documentSummary');
    const summaryRendered = document.getElementById('documentSummaryRendered');
    const summaryLoading = document.querySelector('.summary-loading');

    if (!currentFile) return;

    // Show loading
    summaryLoading.classList.remove('hidden');
    summaryText.value = '';
    summaryRendered.innerHTML = '';

    try {
        // Upload file temporarily to get content
        const formData = new FormData();
        formData.append('file', currentFile);

        const uploadResponse = await fetch('/api/upload?classification=public_company', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error('Failed to process file');
        }

        const uploadData = await uploadResponse.json();
        currentFileId = uploadData.file_id;

        // Request summary generation
        const summaryResponse = await fetch('/api/generate-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: currentFileId })
        });

        if (!summaryResponse.ok) {
            throw new Error('Failed to generate summary');
        }

        const summaryData = await summaryResponse.json();
        const summaryValue = summaryData.summary || '';
        summaryText.value = summaryValue;
        summaryRendered.innerHTML = renderMarkdownSummary(summaryValue);

    } catch (error) {
        console.error('Summary generation error:', error);
        const fallback = `[Summary generation failed: ${error.message}]\n\nYou can edit this field manually with your own summary.`;
        summaryText.value = fallback;
        summaryRendered.textContent = fallback;
    } finally {
        summaryLoading.classList.add('hidden');
    }
}

async function handleUpload() {
    if (!currentFile) {
        alert('Please select a file');
        return;
    }

    // Get form values
    const title = document.getElementById('documentTitle').value;
    const accessLevel = document.getElementById('accessLevel').value;
    const storageMode = document.getElementById('storageMode').value;
    const autoDelete = document.getElementById('autoDelete').checked;
    const summarySource = document.getElementById('documentSummary');
    const summaryRendered = document.getElementById('documentSummaryRendered');
    const summary = summarySource.value || summaryRendered.innerText.trim();

    // Validate
    if (!title.trim()) {
        alert('Please provide a document title');
        return;
    }

    if (storageMode === 'summary' && !summary.trim()) {
        alert('Please generate or enter a summary');
        return;
    }

    // Show progress
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.querySelector('.upload-progress');
    const progressFill = uploadProgress.querySelector('.progress-fill');
    const progressText = uploadProgress.querySelector('.progress-text');

    uploadBtn.disabled = true;
    uploadProgress.classList.remove('hidden');

    try {
        // Upload file with all parameters
        const formData = new FormData();
        formData.append('file', currentFile);

        const params = new URLSearchParams({
            classification: accessLevel,
            title: title,
            storage_mode: storageMode,
            auto_delete: autoDelete.toString(),
        });

        if (storageMode === 'summary') {
            params.append('summary', summary);
        }

        progressFill.style.width = '30%';
        progressText.textContent = 'Uploading...';

        const response = await fetch(`/api/upload-managed?${params.toString()}`, {
            method: 'POST',
            body: formData
        });

        progressFill.style.width = '70%';

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';

        // Show success
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            const uploadSuccess = document.querySelector('.upload-success');
            uploadSuccess.classList.remove('hidden');
        }, 500);

    } catch (error) {
        console.error('Upload error:', error);
        alert(`Upload failed: ${error.message}`);
        uploadBtn.disabled = false;
        uploadProgress.classList.add('hidden');
    }
}

function resetForm() {
    currentFile = null;
    currentFileId = null;

    // Reset UI
    const uploadArea = document.querySelector('.upload-area');
    const uploadDetails = document.querySelector('.upload-details');
    const fileInput = document.getElementById('documentFile');
    const titleInput = document.getElementById('documentTitle');
    const accessLevelSelect = document.getElementById('accessLevel');
    const storageModeSelect = document.getElementById('storageMode');
    const autoDeleteCheckbox = document.getElementById('autoDelete');
    const summarySection = document.querySelector('.summary-section');
    const summaryText = document.getElementById('documentSummary');
    const summaryRendered = document.getElementById('documentSummaryRendered');
    const uploadProgress = document.querySelector('.upload-progress');
    const uploadSuccess = document.querySelector('.upload-success');
    const uploadBtn = document.getElementById('uploadBtn');

    fileInput.value = '';
    titleInput.value = '';
    accessLevelSelect.selectedIndex = 0;
    storageModeSelect.selectedIndex = 0;
    autoDeleteCheckbox.checked = false;
    summaryText.value = '';
    summaryRendered.innerHTML = '';

    uploadArea.classList.remove('hidden');
    uploadDetails.classList.add('hidden');
    summarySection.classList.add('hidden');
    uploadProgress.classList.add('hidden');
    uploadSuccess.classList.add('hidden');

    uploadBtn.disabled = false;
}

function generateTitleFromFilename(filename) {
    // Remove extension and convert to title case
    const nameWithoutExt = filename.replace(/\.[^/.]+$/, '');
    const title = nameWithoutExt.replace(/[-_]/g, ' ');

    // Add date stamp
    const now = new Date();
    const monthYear = now.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

    return `${title} - ${monthYear}`;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function applyInlineMarkdown(line) {
    let text = escapeHtml(line);
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    text = text.replace(/`(.+?)`/g, '<code>$1</code>');
    return text;
}

function renderTableBlock(lines) {
    if (lines.length < 2) return lines.map((l) => `<p>${applyInlineMarkdown(l)}</p>`).join('');

    const rows = lines.map((line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim()));
    const separator = rows[1].every((cell) => /^:?-{3,}:?$/.test(cell));
    if (!separator) return lines.map((l) => `<p>${applyInlineMarkdown(l)}</p>`).join('');

    const header = rows[0];
    const body = rows.slice(2);
    const thead = `<thead><tr>${header.map((cell) => `<th>${applyInlineMarkdown(cell)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${applyInlineMarkdown(cell)}</td>`).join('')}</tr>`).join('')}</tbody>`;
    return `<table>${thead}${tbody}</table>`;
}

function renderMarkdownSummary(markdown) {
    const lines = (markdown || '').replace(/\r\n/g, '\n').split('\n');
    const html = [];

    let i = 0;
    while (i < lines.length) {
        const line = lines[i];

        if (!line.trim()) {
            i += 1;
            continue;
        }

        if (line.includes('|') && i + 1 < lines.length && lines[i + 1].includes('|')) {
            const tableLines = [line];
            i += 1;
            while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
                tableLines.push(lines[i]);
                i += 1;
            }
            html.push(renderTableBlock(tableLines));
            continue;
        }

        if (/^\s*[-*]\s+/.test(line)) {
            const items = [];
            while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
                items.push(lines[i].replace(/^\s*[-*]\s+/, ''));
                i += 1;
            }
            html.push(`<ul>${items.map((item) => `<li>${applyInlineMarkdown(item)}</li>`).join('')}</ul>`);
            continue;
        }

        if (/^\s*\d+\.\s+/.test(line)) {
            const items = [];
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
                items.push(lines[i].replace(/^\s*\d+\.\s+/, ''));
                i += 1;
            }
            html.push(`<ol>${items.map((item) => `<li>${applyInlineMarkdown(item)}</li>`).join('')}</ol>`);
            continue;
        }

        html.push(`<p>${applyInlineMarkdown(line)}</p>`);
        i += 1;
    }

    return html.join('');
}
