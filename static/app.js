/**
 * AgentLens - Live Multi-Agent Analysis UI
 * With structured step descriptions and real-time progress
 */

// DOM Elements
const inputSection = document.getElementById('inputSection');
const progressSection = document.getElementById('progressSection');
const reportSection = document.getElementById('reportSection');
const errorSection = document.getElementById('errorSection');
const analyzeForm = document.getElementById('analyzeForm');
const repoUrlInput = document.getElementById('repoUrl');
const inputWrapper = document.getElementById('inputWrapper');
const inputError = document.getElementById('inputError');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnHint = document.getElementById('btnHint');
const progressStatus = document.getElementById('progressStatus');
const progressTime = document.getElementById('progressTime');
const progressBar = document.getElementById('progressBarFill');
const progressStep = document.getElementById('progressStep');
const agentCards = document.getElementById('agentCards');
const mcpCalls = document.getElementById('mcpCalls');
const reportContent = document.getElementById('reportContent');
const errorMessage = document.getElementById('errorMessage');
const errorDetails = document.getElementById('errorDetails');
const errorTips = document.getElementById('errorTips');

// State
let currentReport = '';
let analysisTimer = null;
let analysisSeconds = 0;
let currentStepNumber = 0;
const totalSteps = 8;

// Agent info for display
const agentInfo = {
    'RepositoryValidator': { icon: '🔗', color: '#6366f1' },
    'FileGatherer': { icon: '📁', color: '#3b82f6' },
    'CodeScanner': { icon: '🔍', color: '#8b5cf6' },
    'MCPFetcher': { icon: '📡', color: '#a855f7' },
    'BestPracticesChecker': { icon: '✅', color: '#10b981' },
    'SlopDetector': { icon: '🚨', color: '#f59e0b' },
    'Optimizer': { icon: '⚡', color: '#06b6d4' },
    'ReportCompiler': { icon: '📝', color: '#ec4899' }
};

// Validation
function validateGitHubUrl(url) {
    if (!url) return { valid: false, error: 'Please enter a GitHub repository URL' };
    const githubPattern = /^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+\/?$/i;
    if (!githubPattern.test(url)) {
        return { valid: false, error: 'Invalid GitHub URL. Format: https://github.com/owner/repo' };
    }
    return { valid: true, error: null };
}

function showInputError(message) {
    inputWrapper.classList.add('error');
    inputError.textContent = message;
    inputError.classList.remove('hidden');
    repoUrlInput.setAttribute('aria-invalid', 'true');
}

function clearInputError() {
    inputWrapper.classList.remove('error');
    inputError.classList.add('hidden');
    inputError.textContent = '';
    repoUrlInput.setAttribute('aria-invalid', 'false');
}

function setButtonLoading(loading) {
    if (loading) {
        analyzeBtn.disabled = true;
        analyzeBtn.classList.add('loading');
        analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing...';
        analyzeBtn.querySelector('.btn-icon').classList.add('hidden');
        analyzeBtn.querySelector('.btn-spinner').classList.remove('hidden');
        btnHint.classList.remove('hidden');
    } else {
        analyzeBtn.disabled = false;
        analyzeBtn.classList.remove('loading');
        analyzeBtn.querySelector('.btn-text').textContent = 'Analyze Repository';
        analyzeBtn.querySelector('.btn-icon').classList.remove('hidden');
        analyzeBtn.querySelector('.btn-spinner').classList.add('hidden');
        btnHint.classList.add('hidden');
    }
}

// Timer
function startTimer() {
    analysisSeconds = 0;
    updateTimerDisplay();
    analysisTimer = setInterval(() => {
        analysisSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (analysisTimer) {
        clearInterval(analysisTimer);
        analysisTimer = null;
    }
}

function updateTimerDisplay() {
    const mins = Math.floor(analysisSeconds / 60);
    const secs = analysisSeconds % 60;
    progressTime.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    analyzeForm.addEventListener('submit', handleAnalyze);

    repoUrlInput.addEventListener('input', () => {
        if (inputWrapper.classList.contains('error')) {
            const validation = validateGitHubUrl(repoUrlInput.value.trim());
            if (validation.valid) clearInputError();
        }
    });

    repoUrlInput.addEventListener('blur', () => {
        const url = repoUrlInput.value.trim();
        if (url) {
            const validation = validateGitHubUrl(url);
            if (!validation.valid) showInputError(validation.error);
            else clearInputError();
        }
    });

    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            repoUrlInput.value = btn.dataset.url;
            clearInputError();
            handleAnalyze(new Event('submit'));
        });
    });

    document.getElementById('backBtn').addEventListener('click', resetUI);
    document.getElementById('retryBtn').addEventListener('click', resetUI);

    document.getElementById('copyBtn').addEventListener('click', () => {
        navigator.clipboard.writeText(currentReport).then(() => {
            const btn = document.getElementById('copyBtn');
            btn.innerHTML = '<span aria-hidden="true">✓</span> Copied!';
            setTimeout(() => btn.innerHTML = '<span aria-hidden="true">📋</span> Copy', 2000);
        });
    });

    document.getElementById('downloadBtn').addEventListener('click', () => {
        const blob = new Blob([currentReport], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'agentlens_report.md';
        a.click();
        URL.revokeObjectURL(url);
    });

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (!inputSection.classList.contains('hidden')) {
                analyzeForm.dispatchEvent(new Event('submit'));
            }
        }
        if (e.key === 'Escape') {
            if (!progressSection.classList.contains('hidden') ||
                !reportSection.classList.contains('hidden') ||
                !errorSection.classList.contains('hidden')) {
                resetUI();
            }
        }
    });
});

function handleAnalyze(e) {
    e.preventDefault();
    const url = repoUrlInput.value.trim();
    const validation = validateGitHubUrl(url);
    if (!validation.valid) {
        showInputError(validation.error);
        repoUrlInput.focus();
        return;
    }
    clearInputError();
    startAnalysis(url);
}

function startAnalysis(repoUrl) {
    currentStepNumber = 0;
    setButtonLoading(true);
    showSection('progress');
    agentCards.innerHTML = '';
    mcpCalls.innerHTML = '';
    progressStatus.textContent = 'Connecting to analysis server...';
    progressBar.style.width = '0%';
    progressStep.textContent = 'Step 0 of 8';
    startTimer();

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/analyze`);

    ws.onopen = () => {
        progressStatus.textContent = 'Starting multi-agent analysis...';
        ws.send(JSON.stringify({ repo_url: repoUrl }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onerror = () => {
        stopTimer();
        setButtonLoading(false);
        showError('Connection failed', [
            'Check your internet connection',
            'Make sure the server is running on localhost:8000',
            'Try refreshing the page'
        ]);
    };

    ws.onclose = () => {
        setButtonLoading(false);
    };
}

function handleMessage(data) {
    switch (data.type) {
        case 'step':
            handleStep(data);
            break;
        case 'mcp_tool':
            handleMcpTool(data);
            break;
        case 'complete':
            stopTimer();
            setButtonLoading(false);
            currentReport = data.report;
            showReport(data.report);
            break;
        case 'error':
            stopTimer();
            setButtonLoading(false);
            handleError(data.message);
            break;
    }
}

function handleStep(data) {
    const { step_number, agent_name, status, description, detail } = data;
    const info = agentInfo[agent_name] || { icon: '🤖', color: '#6b7280' };

    // Update progress bar
    currentStepNumber = step_number;
    const percent = Math.min((step_number / totalSteps) * 100, 100);
    progressBar.style.width = `${percent}%`;
    document.getElementById('progressBar').setAttribute('aria-valuenow', percent);
    progressStep.textContent = `Step ${step_number} of ${totalSteps}`;

    let card = document.getElementById(`step-${step_number}`);

    if (!card) {
        card = document.createElement('div');
        card.id = `step-${step_number}`;
        card.className = 'agent-card';
        card.setAttribute('role', 'listitem');
        card.innerHTML = `
            <div class="agent-header" style="border-left: 4px solid ${info.color}">
                <span class="step-number">${step_number}</span>
                <span class="agent-icon" aria-hidden="true">${info.icon}</span>
                <div class="agent-info">
                    <h4 class="agent-name">${agent_name}</h4>
                    <span class="agent-desc">${description}</span>
                </div>
                <span class="agent-indicator" aria-label="Status"></span>
            </div>
            <div class="agent-detail" aria-live="polite">${detail}</div>
        `;
        agentCards.appendChild(card);
    }

    const descEl = card.querySelector('.agent-desc');
    const detailEl = card.querySelector('.agent-detail');
    const indicator = card.querySelector('.agent-indicator');

    descEl.textContent = description;
    detailEl.textContent = detail;

    if (status === 'in_progress') {
        card.classList.add('running');
        card.classList.remove('complete', 'error');
        indicator.innerHTML = '<span class="spinner-small" aria-label="Running"></span>';
        progressStatus.textContent = `${info.icon} ${description}`;
    } else if (status === 'completed') {
        card.classList.remove('running');
        card.classList.add('complete');
        indicator.innerHTML = '<span aria-label="Complete">✓</span>';
    } else if (status === 'error') {
        card.classList.remove('running');
        card.classList.add('error');
        indicator.innerHTML = '<span aria-label="Error">✗</span>';
    }

    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleMcpTool(data) {
    const { server, tool, query, result, status } = data;

    if (status === 'calling') {
        const call = document.createElement('div');
        call.className = 'mcp-call calling';
        call.dataset.server = server;
        call.dataset.query = query;
        call.innerHTML = `
            <div class="mcp-header">
                <span class="mcp-server">${server}</span>
                <span class="mcp-tool">${tool}</span>
                <span class="mcp-status"><span class="spinner-small" aria-label="Loading"></span></span>
            </div>
            <div class="mcp-query">Query: "${escapeHtml(query.substring(0, 60))}${query.length > 60 ? '...' : ''}"</div>
            <div class="mcp-result hidden"></div>
        `;
        mcpCalls.appendChild(call);
        mcpCalls.scrollTop = mcpCalls.scrollHeight;
    } else {
        const calls = mcpCalls.querySelectorAll('.mcp-call.calling');
        for (const call of calls) {
            if (call.dataset.server === server && call.dataset.query === query) {
                call.classList.remove('calling');
                call.classList.add(status);
                call.querySelector('.mcp-status').innerHTML = status === 'complete' ?
                    '<span aria-label="Complete">✓</span>' : '<span aria-label="Error">✗</span>';
                if (result) {
                    const resultEl = call.querySelector('.mcp-result');
                    resultEl.classList.remove('hidden');
                    resultEl.textContent = result.substring(0, 200) + (result.length > 200 ? '...' : '');
                }
                break;
            }
        }
    }
}

function handleError(message) {
    let tips = [];
    if (message.includes('rate limit')) {
        tips = ['GitHub API rate limit exceeded', 'Add a GITHUB_TOKEN to your .env file', 'Wait a few minutes and try again'];
    } else if (message.includes('not found') || message.includes('404')) {
        tips = ['Check that the repository URL is correct', 'Make sure the repository is public', 'Verify the owner and repo name spelling'];
    } else if (message.includes('token') || message.includes('429')) {
        tips = ['OpenAI rate limit reached', 'Wait a minute and try again', 'Consider using a smaller repository'];
    } else {
        tips = ['Check your internet connection', 'Make sure the repository URL is valid', 'Try again in a few moments'];
    }
    showError(message, tips);
}

function showError(message, tips = []) {
    showSection('error');
    errorMessage.textContent = message;
    if (tips.length > 0) {
        errorDetails.classList.remove('hidden');
        errorTips.innerHTML = tips.map(tip => `<li>${tip}</li>`).join('');
    } else {
        errorDetails.classList.add('hidden');
    }
}

function showReport(markdown) {
    showSection('report');
    reportContent.innerHTML = marked.parse(markdown);
    document.querySelectorAll('pre code').forEach((block) => {
        Prism.highlightElement(block);
    });
    reportContent.focus();
}

function showSection(section) {
    inputSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    reportSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    switch (section) {
        case 'input': inputSection.classList.remove('hidden'); break;
        case 'progress': progressSection.classList.remove('hidden'); break;
        case 'report': reportSection.classList.remove('hidden'); break;
        case 'error': errorSection.classList.remove('hidden'); break;
    }
}

function resetUI() {
    stopTimer();
    setButtonLoading(false);
    showSection('input');
    repoUrlInput.value = '';
    clearInputError();
    agentCards.innerHTML = '';
    mcpCalls.innerHTML = '';
    currentStepNumber = 0;
    repoUrlInput.focus();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
