/**
 * Cold Email Personalizer — Frontend
 * Handles form submission, result display, clipboard, history, and sample loading.
 */

const form           = document.getElementById('prospect-form');
const btnGenerate    = document.getElementById('btn-generate');
const btnCopy        = document.getElementById('btn-copy');
const btnRetry       = document.getElementById('btn-retry');

const emptyState     = document.getElementById('empty-state');
const loadingState   = document.getElementById('loading-state');
const resultState    = document.getElementById('result-state');
const errorState     = document.getElementById('error-state');

const resultSubject  = document.getElementById('result-subject');
const resultBody     = document.getElementById('result-body');
const wordCountBadge = document.getElementById('word-count-badge');
const wordCountValue = document.getElementById('word-count-value');
const errorMessage   = document.getElementById('error-message');

const historySection = document.getElementById('history-section');
const historyGrid    = document.getElementById('history-grid');
const historyCount   = document.getElementById('history-count');

const toast          = document.getElementById('toast');
const toastText      = document.getElementById('toast-text');

// State
const sessionHistory = [];
let currentResult    = null;


// --- State switching ---
function showState(state) {
    [emptyState, loadingState, resultState, errorState].forEach(el => el.classList.add('hidden'));
    state.classList.remove('hidden');
}


// --- Form submission ---
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await generateEmail();
});

async function generateEmail() {
    const formData = new FormData(form);
    const prospect = Object.fromEntries(formData.entries());

    const fields = ['name', 'role', 'company', 'company_industry', 'recent_achievement', 'linkedin_headline'];
    for (const field of fields) {
        if (!prospect[field] || !prospect[field].trim()) {
            showToast('Please fill in all fields');
            return;
        }
    }

    showState(loadingState);
    btnGenerate.disabled = true;
    btnGenerate.querySelector('.btn-label').textContent = 'Generating...';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prospect),
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Unknown error');
        }

        currentResult = { ...data, prospect };
        displayResult(data);
        addToHistory(prospect, data);

    } catch (err) {
        showState(errorState);
        errorMessage.textContent = err.message;
    } finally {
        btnGenerate.disabled = false;
        btnGenerate.querySelector('.btn-label').textContent = 'Generate Email';
    }
}


// --- Display result ---
function displayResult(data) {
    showState(resultState);

    resultSubject.textContent = data.subject_line;
    resultBody.textContent = data.opening_lines;

    const wc = data.word_count;
    wordCountValue.textContent = wc;
    wordCountBadge.className = 'wc-pill ' + (wc <= 50 ? 'under' : 'over');

    resetCopyButton();
}


// --- Clipboard ---
btnCopy.addEventListener('click', async () => {
    if (!currentResult) return;

    const text = `Subject: ${currentResult.subject_line}\n\n${currentResult.opening_lines}`;

    try {
        await navigator.clipboard.writeText(text);
    } catch {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
    }

    btnCopy.classList.add('copied');
    btnCopy.querySelector('.icon-copy').classList.add('hidden');
    btnCopy.querySelector('.icon-check').classList.remove('hidden');
    btnCopy.querySelector('.copy-label').textContent = 'Copied';
    showToast('Copied to clipboard');
    setTimeout(resetCopyButton, 2000);
});

function resetCopyButton() {
    btnCopy.classList.remove('copied');
    btnCopy.querySelector('.icon-copy').classList.remove('hidden');
    btnCopy.querySelector('.icon-check').classList.add('hidden');
    btnCopy.querySelector('.copy-label').textContent = 'Copy';
}


// --- Retry ---
btnRetry.addEventListener('click', () => showState(emptyState));


// --- History ---
function addToHistory(prospect, data) {
    sessionHistory.unshift({ prospect, data, timestamp: new Date() });
    renderHistory();
}

function renderHistory() {
    if (sessionHistory.length === 0) {
        historySection.classList.add('hidden');
        return;
    }

    historySection.classList.remove('hidden');
    historyCount.textContent = sessionHistory.length;

    historyGrid.innerHTML = sessionHistory.map(entry => {
        const time = entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return `
            <div class="history-item">
                <div class="history-item-head">
                    <span class="history-name">${esc(entry.prospect.name)} — ${esc(entry.prospect.role)}</span>
                    <span class="history-time">${time}</span>
                </div>
                <div class="history-subj">${esc(entry.data.subject_line)}</div>
                <div class="history-excerpt">${esc(entry.data.opening_lines)}</div>
            </div>
        `;
    }).join('');
}


// --- Toast ---
let toastTimer = null;

function showToast(message) {
    if (toastTimer) clearTimeout(toastTimer);
    toastText.textContent = message;
    toast.classList.remove('hidden');
    toastTimer = setTimeout(() => toast.classList.add('hidden'), 2500);
}


// --- Utility ---
function esc(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}
