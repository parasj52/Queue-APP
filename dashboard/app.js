// Extracted JS from dashboard/index.html
const API_BASE = 'http://localhost:5000';
let CURRENT_USER = null;

function showLogin() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('dashboard-content').classList.add('hidden');
    document.getElementById('top-actions').style.display = 'none';
}
function showDashboard() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('dashboard-content').classList.remove('hidden');
    document.getElementById('top-actions').style.display = 'flex';
    document.getElementById('welcome-text').textContent = `Signed in as ${CURRENT_USER}`;
}

function requireAuthHeaders() {
    return { 'X-User': CURRENT_USER };
}

async function fetchJobs() {
    if (!CURRENT_USER) return;
    document.getElementById('jobs-loading').style.display = '';
    try {
        let res = await fetch(API_BASE + '/jobs', {headers: requireAuthHeaders()});
        let data = await res.json();
        let html = '';
        for (let job of data.jobs) {
            html += `<div class="job-card">
                <div><span class="badge ${job.status}">${job.status.toUpperCase()}</span></div>
                <div class="job-id">${job.id}</div>
                <div>Retries: <b>${job.retries}</b></div>
            </div>`;
        }
        document.getElementById('jobs').innerHTML = html;
        document.getElementById('job-count').textContent = data.jobs.length;
    } catch (e) {
        document.getElementById('jobs').innerHTML = '<div class="loading">Error loading jobs.</div>';
        document.getElementById('job-count').textContent = '';
    }
    document.getElementById('jobs-loading').style.display = 'none';
}
async function fetchDLQ() {
    if (!CURRENT_USER) return;
    document.getElementById('dlq-loading').style.display = '';
    try {
        let res = await fetch(API_BASE + '/dlq', { headers: requireAuthHeaders() });
        let data = await res.json();
        let html = '';
        for (let item of data.dlq) {
            html += `<div class="job-card">
                <div><span class="badge failed">FAILED</span></div>
                <div class="job-id">${item.id}</div>
                <div class="dlq-reason">${item.reason}</div>
            </div>`;
        }
        document.getElementById('dlq').innerHTML = html;
        document.getElementById('dlq-count').textContent = data.dlq.length;
    } catch (e) {
        document.getElementById('dlq').innerHTML = '<div class="loading">Error loading DLQ.</div>';
        document.getElementById('dlq-count').textContent = '';
    }
    document.getElementById('dlq-loading').style.display = 'none';
}

// Login flow
document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const user = document.getElementById('login-user').value.trim();
    if (!user) return alert('Please enter a username');
    // store in localStorage to simulate authentication state
    localStorage.setItem('jq_user', user);
    CURRENT_USER = user;
    showDashboard();
    // kick off polling
    fetchJobs(); fetchDLQ();
});

// Logout
document.getElementById('logout-button').addEventListener('click', () => {
    localStorage.removeItem('jq_user');
    CURRENT_USER = null;
    showLogin();
});

// Submit job from dashboard
document.getElementById('submit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const idempotency = document.getElementById('input-idempotency').value.trim();
    const payloadText = document.getElementById('input-payload').value;
    let payload;
    try {
        payload = JSON.parse(payloadText);
    } catch (err) {
        document.getElementById('submit-result').textContent = 'Invalid JSON payload';
        document.getElementById('submit-result').style.color = '#de350b';
        return;
    }
    const body = { payload };
    if (idempotency) body.idempotency_key = idempotency;
    try {
        const res = await fetch(API_BASE + '/jobs', {
            method: 'POST',
            headers: Object.assign({'Content-Type': 'application/json'}, requireAuthHeaders()),
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (!res.ok) {
            document.getElementById('submit-result').textContent = data.error || 'Error submitting job';
            document.getElementById('submit-result').style.color = '#de350b';
        } else {
            document.getElementById('submit-result').textContent = `Created job ${data.job_id} (${data.status})`;
            document.getElementById('submit-result').style.color = '#00875a';
            // refresh lists
            fetchJobs(); fetchDLQ();
        }
    } catch (err) {
        document.getElementById('submit-result').textContent = 'Network error';
        document.getElementById('submit-result').style.color = '#de350b';
    }
    // clear idempotency key to avoid accidental reuse
    // document.getElementById('input-idempotency').value = '';
});

// Initialization: check localStorage and show appropriate view
(function init() {
    const stored = localStorage.getItem('jq_user');
    if (stored) {
        CURRENT_USER = stored;
        showDashboard();
        // start polling only when logged in
        setInterval(() => { fetchJobs(); fetchDLQ(); }, 2000);
        fetchJobs(); fetchDLQ();
    } else {
        showLogin();
    }
})();
