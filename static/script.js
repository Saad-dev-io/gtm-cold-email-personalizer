/**
 * GTM Cold Email Personalizer — Frontend Logic
 * ==============================================
 * Handles form submission, API calls, result display,
 * clipboard copy, session history, and sample loading.
 */

// ─── DOM Elements ───
const form = document.getElementById('prospect-form');
const btnGenerate = document.getElementById('btn-generate');
const btnLoadSample = document.getElementById('btn-load-sample');
const btnCopy = document.getElementById('btn-copy');
const btnRetry = document.getElementById('btn-retry');

const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const resultState = document.getElementById('result-state');
const errorState = document.getElementById('error-state');

const resultSubject = document.getElementById('result-subject');
const resultBody = document.getElementById('result-body');
const wordCountBadge = document.getElementById('word-count-badge');
const wordCountValue = document.getElementById('word-count-value');
const errorMessage = document.getElementById('error-message');

const historySection = document.getElementById('history-section');
const historyGrid = document.getElementById('history-grid');
const historyCount = document.getElementById('history-count');

const toast = document.getElementById('toast');
const toastText = document.getElementById('toast-text');

// ─── State ───
const sessionHistory = [];
let sampleProspects = [];
let sampleIndex = 0;
let currentResult = null;


// ─── State Management ───
function showState(state) {
    [emptyState, loadingState, resultState, errorState].forEach(el => el.classList.add('hidden'));
    state.classList.remove('hidden');
}


// ─── Form Submission ───
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await generateEmail();
});

async function generateEmail() {
    // Collect form data
    const formData = new FormData(form);
    const prospect = Object.fromEntries(formData.entries());

    // Validate
    const fields = ['name', 'role', 'company', 'company_industry', 'recent_achievement', 'linkedin_headline'];
    for (const field of fields) {
        if (!prospect[field] || !prospect[field].trim()) {
            showToast('Please fill in all fields', true);
            return;
        }
    }

    // Show loading
    showState(loadingState);
    btnGenerate.disabled = true;
    btnGenerate.querySelector('.btn-text').textContent = 'Generating...';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prospect),
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Unknown error occurred');
        }

        // Display result
        currentResult = { ...data, prospect };
        displayResult(data);

        // Add to history
        addToHistory(prospect, data);

    } catch (err) {
        showState(errorState);
        errorMessage.textContent = err.message;
    } finally {
        btnGenerate.disabled = false;
        btnGenerate.querySelector('.btn-text').textContent = 'Generate Email';
    }
}


// ─── Display Result ───
function displayResult(data) {
    showState(resultState);

    resultSubject.textContent = data.subject_line;
    resultBody.textContent = `"${data.opening_lines}"`;

    const wc = data.word_count;
    wordCountValue.textContent = wc;

    if (wc <= 50) {
        wordCountBadge.className = 'word-count-badge under-limit';
    } else {
        wordCountBadge.className = 'word-count-badge over-limit';
    }

    // Reset copy button
    resetCopyButton();
}


// ─── Copy to Clipboard ───
btnCopy.addEventListener('click', async () => {
    if (!currentResult) return;

    const text = `Subject: ${currentResult.subject_line}\n\n${currentResult.opening_lines}`;

    try {
        await navigator.clipboard.writeText(text);

        // Show checkmark animation
        btnCopy.classList.add('copied');
        btnCopy.querySelector('.copy-icon').classList.add('hidden');
        btnCopy.querySelector('.check-icon').classList.remove('hidden');
        btnCopy.querySelector('.copy-text').textContent = 'Copied!';

        showToast('Copied to clipboard!');

        // Reset after 2s
        setTimeout(resetCopyButton, 2000);
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        btnCopy.classList.add('copied');
        btnCopy.querySelector('.copy-text').textContent = 'Copied!';
        showToast('Copied to clipboard!');
        setTimeout(resetCopyButton, 2000);
    }
});

function resetCopyButton() {
    btnCopy.classList.remove('copied');
    btnCopy.querySelector('.copy-icon').classList.remove('hidden');
    btnCopy.querySelector('.check-icon').classList.add('hidden');
    btnCopy.querySelector('.copy-text').textContent = 'Copy';
}


// ─── Retry Button ───
btnRetry.addEventListener('click', () => {
    showState(emptyState);
});


// ─── Session History ───
function addToHistory(prospect, data) {
    const entry = {
        prospect,
        data,
        timestamp: new Date(),
    };
    sessionHistory.unshift(entry);
    renderHistory();
}

function renderHistory() {
    if (sessionHistory.length === 0) {
        historySection.classList.add('hidden');
        return;
    }

    historySection.classList.remove('hidden');
    historyCount.textContent = `${sessionHistory.length} email${sessionHistory.length > 1 ? 's' : ''}`;

    historyGrid.innerHTML = sessionHistory.map((entry, i) => {
        const time = entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return `
            <div class="history-card" style="animation-delay: ${i * 0.05}s">
                <div class="history-card-header">
                    <span class="history-prospect">${escapeHtml(entry.prospect.name)} — ${escapeHtml(entry.prospect.role)}</span>
                    <span class="history-time">${time}</span>
                </div>
                <div class="history-subject">${escapeHtml(entry.data.subject_line)}</div>
                <div class="history-body">"${escapeHtml(entry.data.opening_lines)}"</div>
            </div>
        `;
    }).join('');
}


// ─── Load Sample ───
btnLoadSample.addEventListener('click', async () => {
    if (sampleProspects.length === 0) {
        try {
            const res = await fetch('/samples');
            sampleProspects = await res.json();
        } catch {
            showToast('Could not load sample data', true);
            return;
        }
    }

    if (sampleProspects.length === 0) return;

    const sample = sampleProspects[sampleIndex % sampleProspects.length];
    sampleIndex++;

    // Fill form fields
    document.getElementById('input-name').value = sample.name || '';
    document.getElementById('input-role').value = sample.role || '';
    document.getElementById('input-company').value = sample.company || '';
    document.getElementById('input-industry').value = sample.company_industry || '';
    document.getElementById('input-achievement').value = sample.recent_achievement || '';
    document.getElementById('input-headline').value = sample.linkedin_headline || '';

    // Add a subtle animation to show the fields were filled
    form.querySelectorAll('input, textarea').forEach((el, i) => {
        el.style.transition = 'none';
        el.style.borderColor = 'rgba(124, 58, 237, 0.5)';
        setTimeout(() => {
            el.style.transition = 'border-color 0.5s ease';
            el.style.borderColor = '';
        }, 300 + i * 50);
    });

    showToast(`Loaded sample: ${sample.name}`);
});


// ─── Toast Notifications ───
let toastTimeout = null;

function showToast(message, isError = false) {
    if (toastTimeout) clearTimeout(toastTimeout);

    toastText.textContent = message;
    const toastIcon = toast.querySelector('.toast-icon');
    toastIcon.textContent = isError ? '!' : '✓';
    toastIcon.style.background = isError ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)';
    toastIcon.style.color = isError ? '#ef4444' : '#22c55e';

    toast.classList.remove('hidden');

    toastTimeout = setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}


// ─── Utility ───
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
