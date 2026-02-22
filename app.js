/**
 * FinGuard AI - Dashboard Logic
 * Integrates with FastAPI backend for real-time risk analytics.
 */

const API_BASE = 'http://localhost:8000';
const POLLING_INTERVAL = 2000;

let allTransactions = [];
let highRiskAlerts = [];
let selectedTxn = null;

// DOM Elements
const txnFeed = document.getElementById('txn-feed');
const alertCountEl = document.getElementById('alert-count');
const avgHealthEl = document.getElementById('avg-health');
const globalRiskEl = document.getElementById('global-risk-level');
const backendStatusEl = document.getElementById('backend-status');
const explanationBox = document.getElementById('explanation-box');
const evidenceBox = document.getElementById('evidence-box');
const insightTxnId = document.getElementById('insight-txn-id');
const riskCategoryBox = document.getElementById('risk-category-tags');
const currentUserIdEl = document.getElementById('current-user-id');

/**
 * Fetch data from API
 */
async function fetchData() {
    try {
        const [txnsResponse, alertsResponse] = await Promise.all([
            fetch(`${API_BASE}/transactions`),
            fetch(`${API_BASE}/alerts`)
        ]);

        if (!txnsResponse.ok || !alertsResponse.ok) throw new Error('API Unavailable');

        const txns = await txnsResponse.json();
        const alerts = await alertsResponse.json();

        updateDashboard(txns, alerts);
        backendStatusEl.innerText = 'SYSTEM ONLINE';
        backendStatusEl.parentElement.querySelector('.status-dot').style.backgroundColor = '#10b981';
    } catch (error) {
        console.error('Fetch error:', error);
        backendStatusEl.innerText = 'SYSTEM OFFLINE';
        backendStatusEl.parentElement.querySelector('.status-dot').style.backgroundColor = '#f43f5e';
    }
}

/**
 * Update the UI with fresh data
 */
function updateDashboard(txns, alerts) {
    allTransactions = txns;
    highRiskAlerts = alerts;

    // Update Stats
    alertCountEl.innerText = alerts.length;
    
    if (txns.length > 0) {
        const avgHealth = (txns.reduce((acc, t) => acc + t.health_score, 0) / txns.length).toFixed(1);
        avgHealthEl.innerText = avgHealth;
        
        const latestTrend = txns[0].risk_trend;
        globalRiskEl.innerText = latestTrend;
        globalRiskEl.style.color = latestTrend === 'INCREASING' ? '#f43f5e' : (latestTrend === 'DECREASING' ? '#10b981' : '#f8fafc');
    }

    renderTxnList();
}

/**
 * Render the transaction feed
 */
function renderTxnList() {
    if (allTransactions.length === 0) return;

    txnFeed.innerHTML = '';
    allTransactions.forEach(txn => {
        const card = document.createElement('div');
        card.className = 'txn-card glass';
        card.onclick = () => selectTransaction(txn);
        
        if (selectedTxn && selectedTxn.transaction_id === txn.transaction_id) {
            card.style.borderColor = 'var(--accent-primary)';
            card.style.background = 'rgba(99, 102, 241, 0.1)';
        }

        const date = new Date(txn.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        card.innerHTML = `
            <div class="txn-icon">🏦</div>
            <div class="txn-details">
                <span class="merchant-name">${txn.merchant}</span>
                <span class="txn-meta">${txn.location} • ${date}</span>
            </div>
            <div class="txn-amount">$${txn.amount.toLocaleString()}</div>
            <div class="risk-tag risk-${txn.risk_level}">${txn.risk_level}</div>
        `;
        txnFeed.appendChild(card);
    });
}

/**
 * Handle transaction selection for insights
 */
function selectTransaction(txn) {
    selectedTxn = txn;
    renderTxnList(); // Refresh highlighting

    // Update Insight Panel
    insightTxnId.innerText = `Ref: ${txn.transaction_id}`;
    explanationBox.innerText = txn.explanation;
    currentUserIdEl.innerText = `Profile: ${txn.user_id}`;

    // Update Evidence
    evidenceBox.innerHTML = '';
    txn.supporting_evidence.forEach(item => {
        const li = document.createElement('li');
        li.className = 'evidence-item';
        li.innerText = item;
        evidenceBox.appendChild(li);
    });

    // Update Categories
    riskCategoryBox.innerHTML = '';
    txn.risk_category.forEach(cat => {
        const span = document.createElement('span');
        span.className = 'risk-tag';
        span.style.background = 'rgba(255, 255, 255, 0.05)';
        span.style.color = 'var(--text-secondary)';
        span.innerText = cat;
        riskCategoryBox.appendChild(span);
    });
}

// Initialize
fetchData();
setInterval(fetchData, POLLING_INTERVAL);
