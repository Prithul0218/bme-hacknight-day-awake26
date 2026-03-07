const quickAlertForm = document.getElementById('quickAlertForm');
const alertName = document.getElementById('alertName');
const alertMetric = document.getElementById('alertMetric');
const alertCondition = document.getElementById('alertCondition');
const alertThreshold = document.getElementById('alertThreshold');
const alertTimeWindow = document.getElementById('alertTimeWindow');
const alertDepartment = document.getElementById('alertDepartment');
const alertDigestMode = document.getElementById('alertDigestMode');
const createAlertBtn = document.getElementById('createAlertBtn');
const alertsList = document.getElementById('alertsList');
const triggersList = document.getElementById('triggersList');
const alertCountBadge = document.getElementById('alertCount');
const triggerCountBadge = document.getElementById('triggerCount');
const toast = document.getElementById('toast');

let alertsState = [];
let triggersState = [];

const METRIC_LABELS = {
    revenue: 'Revenue',
    operating_expense: 'Operating Expense',
    department_spend: 'Department Spend',
    cash_balance: 'Cash Balance',
    burn_rate: 'Burn Rate',
    ar_aging: 'Accounts Receivable Aging',
    ap_aging: 'Accounts Payable Aging',
    budget_variance_percent: 'Budget Variance %',
};

// Alert Templates
const TEMPLATES = {
    revenue_drop: {
        name: 'Revenue Drop Alert',
        metric: 'revenue',
        condition: '<',
        threshold: 100000,
        severity: 'high',
    },
    expense_spike: {
        name: 'Expense Spike Alert',
        metric: 'operating_expense',
        condition: '>',
        threshold: 50000,
        severity: 'medium',
    },
    budget_overrun: {
        name: 'Budget Overrun Alert',
        metric: 'budget_variance_percent',
        condition: '>',
        threshold: 10,
        severity: 'high',
    },
    cash_low: {
        name: 'Low Cash Alert',
        metric: 'cash_balance',
        condition: '<',
        threshold: 25000,
        severity: 'high',
    },
};

function humanize(value) {
    return String(value || '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (match) => match.toUpperCase());
}

function notify(message, type = 'info') {
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.style.borderLeftColor = type === 'error' ? '#f87171' : '#fe742e';

    clearTimeout(notify.timeout);
    notify.timeout = setTimeout(() => {
        toast.classList.add('hidden');
    }, 3200);
}

function getSelectedSeverity() {
    const activeBtn = document.querySelector('.severity-btn.active');
    return activeBtn ? activeBtn.getAttribute('data-severity') : 'medium';
}

function getSelectedChannels() {
    const activeButtons = document.querySelectorAll('.channel-btn.active');
    return Array.from(activeButtons).map(btn => btn.getAttribute('data-channel'));
}

function renderAlerts() {
    alertCountBadge.textContent = alertsState.length;
    
    if (!alertsState.length) {
        alertsList.innerHTML = `
            <div class="empty-state">
                <span class="material-symbols-outlined">notifications_off</span>
                <p>No alerts yet</p>
            </div>
        `;
        return;
    }

    alertsList.innerHTML = alertsState
        .map((alert) => {
            const scopeLabel = alert.scope_department ? humanize(alert.scope_department) : 'All allowed departments';
            const metricLabel = METRIC_LABELS[alert.metric] || humanize(alert.metric);
            return `
                <article class="alert-card" data-alert-id="${alert.alert_id}">
                    <h3>${alert.alert_name}</h3>
                    <p class="alert-meta">${metricLabel} ${alert.condition} ${alert.threshold_value} · ${humanize(alert.time_window)} · ${scopeLabel}</p>
                    <div class="alert-tags">
                        <span class="tag ${alert.status}">${humanize(alert.status)}</span>
                        <span class="tag">${humanize(alert.severity)}</span>
                        <span class="tag">${humanize(alert.digest_mode)}</span>
                    </div>
                    <div class="alert-actions">
                        <button type="button" class="btn-small" data-action="toggle-status">${alert.status === 'active' ? 'Pause' : 'Activate'}</button>
                        <button type="button" class="btn-small danger" data-action="delete">Delete</button>
                    </div>
                </article>
            `;
        })
        .join('');
}

function renderTriggers(triggers) {
    triggersState = triggers || [];
    triggerCountBadge.textContent = triggersState.length;
    
    if (!triggersState.length) {
        triggersList.innerHTML = `
            <div class="empty-state">
                <span class="material-symbols-outlined">history</span>
                <p>No triggers yet</p>
            </div>
        `;
        return;
    }

    triggersList.innerHTML = triggersState
        .map((trigger) => {
            const when = trigger.triggered_at ? new Date(trigger.triggered_at).toLocaleString() : 'Unknown time';
            return `
                <article class="trigger-card">
                    <p class="alert-meta"><strong>${trigger.alert_name || 'Alert Triggered'}</strong></p>
                    <p class="alert-meta">${trigger.message || 'Triggered event captured.'}</p>
                    <p class="alert-meta">${when}</p>
                </article>
            `;
        })
        .join('');
}

function populateDropdowns(allowedMetrics, allowedDepartments) {
    alertMetric.innerHTML = allowedMetrics
        .map((metric) => `<option value="${metric}">${METRIC_LABELS[metric] || humanize(metric)}</option>`)
        .join('');

    const deptOptions = ['<option value="">All allowed departments</option>']
        .concat(allowedDepartments.map((dept) => `<option value="${dept}">${humanize(dept)}</option>`));
    alertDepartment.innerHTML = deptOptions.join('');
}

async function loadAlertsData() {
    try {
        const response = await fetch('/api/alerts');
        if (!response.ok) {
            throw new Error('Could not load alerts');
        }
        const data = await response.json();
        alertsState = data.alerts || [];
        populateDropdowns(data.allowed_metrics || [], data.allowed_departments || []);
        renderAlerts();
        renderTriggers(data.recent_triggers || []);
    } catch (error) {
        console.error(error);
        notify(error.message || 'Failed to load alerts', 'error');
    }
}

quickAlertForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const channels = getSelectedChannels();
    if (!channels.length) {
        notify('Select at least one delivery channel.', 'error');
        return;
    }

    createAlertBtn.disabled = true;
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                alert_name: alertName.value.trim(),
                metric: alertMetric.value,
                condition: alertCondition.value,
                threshold_value: Number(alertThreshold.value),
                time_window: alertTimeWindow.value,
                scope_department: alertDepartment.value || null,
                severity: getSelectedSeverity(),
                delivery_channels: channels,
                digest_mode: alertDigestMode.value,
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Failed to create alert');
        }

        const createdAlert = await response.json();
        alertsState.unshift(createdAlert);
        renderAlerts();
        quickAlertForm.reset();
        
        // Reset buttons to defaults
        document.querySelectorAll('.severity-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector('.severity-btn[data-severity="medium"]').classList.add('active');
        document.querySelectorAll('.channel-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector('.channel-btn[data-channel="in_app"]').classList.add('active');
        
        notify('Alert created successfully.', 'success');
    } catch (error) {
        console.error(error);
        notify(error.message || 'Failed to create alert', 'error');
    } finally {
        createAlertBtn.disabled = false;
    }
});

alertsList.addEventListener('click', async (event) => {
    const card = event.target.closest('.alert-card');
    if (!card) {
        return;
    }

    const alertId = card.getAttribute('data-alert-id');
    const actionButton = event.target.closest('[data-action]');
    if (!actionButton || !alertId) {
        return;
    }

    const action = actionButton.getAttribute('data-action');

    if (action === 'toggle-status') {
        const alert = alertsState.find((item) => item.alert_id === alertId);
        if (!alert) return;
        const nextStatus = alert.status === 'active' ? 'paused' : 'active';

        try {
            const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: nextStatus }),
            });
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to update alert');
            }
            const updated = await response.json();
            alertsState = alertsState.map((item) => (item.alert_id === alertId ? updated : item));
            renderAlerts();
            notify('Alert status updated.', 'success');
        } catch (error) {
            notify(error.message || 'Failed to update alert', 'error');
        }
    }

    if (action === 'delete') {
        try {
            const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to delete alert');
            }
            alertsState = alertsState.filter((item) => item.alert_id !== alertId);
            renderAlerts();
            notify('Alert deleted.', 'success');
        } catch (error) {
            notify(error.message || 'Failed to delete alert', 'error');
        }
    }
});

// Template button handlers
document.querySelectorAll('.template-card').forEach(btn => {
    btn.addEventListener('click', () => {
        const templateKey = btn.getAttribute('data-template');
        const template = TEMPLATES[templateKey];
        if (template) {
            alertName.value = template.name;
            alertMetric.value = template.metric;
            alertCondition.value = template.condition;
            alertThreshold.value = template.threshold;
            
            // Update severity buttons
            document.querySelectorAll('.severity-btn').forEach(b => b.classList.remove('active'));
            document.querySelector(`.severity-btn[data-severity="${template.severity}"]`)?.classList.add('active');
            
            notify(`Template "${template.name}" loaded`, 'success');
        }
    });
});

// Severity button handlers
document.querySelectorAll('.severity-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.severity-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// Channel button handlers
document.querySelectorAll('.channel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.classList.toggle('active');
    });
});

loadAlertsData();
