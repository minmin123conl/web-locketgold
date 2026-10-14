// Locket Gold Web Tool - Frontend Logic

let currentUID = null;

// DOM Elements
const usernameInput = document.getElementById('username');
const btnResolve = document.getElementById('btn-resolve');
const resolveResult = document.getElementById('resolve-result');
const statusResult = document.getElementById('status-result');
const btnCheckStatus = document.getElementById('btn-check-status');
const btnInject = document.getElementById('btn-inject');
const injectResult = document.getElementById('inject-result');
const keepGoldResult = document.getElementById('keep-gold-result');
const keepGoldContent = document.getElementById('keep-gold-content');
const configInfo = document.getElementById('config-info');

// Progress steps
const progressSteps = document.querySelectorAll('.progress-step');
const stepSections = document.querySelectorAll('.step-section');

// Helper: Show result box
function showResult(element, type, message) {
    element.className = `result-box ${type}`;
    element.innerHTML = message;
    element.classList.remove('hidden');
}

// Helper: Hide result box
function hideResult(element) {
    element.classList.add('hidden');
    element.innerHTML = '';
}

// Helper: Set loading state
function setLoading(button, loading, text) {
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="btn-icon">⏳</span><span class="btn-text">${text || 'Đang xử lý...'}</span>`;
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.disabled = false;
    }
}

// Helper: Update progress bar
function updateProgress(step) {
    progressSteps.forEach((el, index) => {
        const stepNum = index + 1;
        el.classList.remove('active', 'completed');
        if (stepNum < step) {
            el.classList.add('completed');
        } else if (stepNum === step) {
            el.classList.add('active');
        }
    });
    
    stepSections.forEach((el, index) => {
        const stepNum = index + 1;
        el.classList.remove('active');
        if (stepNum === step) {
            el.classList.add('active');
        }
    });
}

// Step 1: Resolve UID
btnResolve.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    if (!username) {
        showResult(resolveResult, 'error', '❌ Vui lòng nhập username hoặc link Locket.');
        return;
    }

    setLoading(btnResolve, true, 'Đang phân giải...');
    hideResult(resolveResult);
    hideResult(statusResult);
    hideResult(injectResult);
    hideResult(keepGoldResult);
    keepGoldContent.classList.add('hidden');
    btnCheckStatus.classList.add('hidden');
    btnInject.classList.add('hidden');
    currentUID = null;

    try {
        const response = await fetch('/api/resolve', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': CSRF_TOKEN
            },
            body: JSON.stringify({ username })
        });
        const data = await response.json();

        if (data.ok) {
            currentUID = data.uid;
            showResult(resolveResult, 'success', `✅ UID: <code>${data.uid}</code>`);
            btnCheckStatus.classList.remove('hidden');
            updateProgress(2);
        } else {
            showResult(resolveResult, 'error', `❌ ${data.error || 'Không tìm thấy UID.'}`);
        }
    } catch (error) {
        showResult(resolveResult, 'error', `❌ Lỗi: ${error.message}`);
    } finally {
        setLoading(btnResolve, false);
    }
});

// Enter key to resolve
usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        btnResolve.click();
    }
});

// Step 2: Check Status
btnCheckStatus.addEventListener('click', async () => {
    if (!currentUID) return;

    setLoading(btnCheckStatus, true, 'Đang kiểm tra...');
    hideResult(statusResult);

    try {
        const response = await fetch(`/api/status/${currentUID}`);
        const data = await response.json();

        if (data.ok) {
            const status = data.status;
            if (status.active) {
                const expires = status.expires ? new Date(status.expires).toLocaleString('vi-VN') : 'Không xác định';
                showResult(statusResult, 'success', `✅ Gold đang hoạt động!<br>Hết hạn: ${expires}`);
                btnInject.classList.add('hidden');
                // Show keep gold section
                showKeepGold();
                updateProgress(4);
            } else {
                showResult(statusResult, 'info', 'ℹ️ Gold chưa được kích hoạt.');
                btnInject.classList.remove('hidden');
                updateProgress(3);
            }
        } else {
            showResult(statusResult, 'error', `❌ ${data.error || 'Không thể kiểm tra.'}`);
        }
    } catch (error) {
        showResult(statusResult, 'error', `❌ Lỗi: ${error.message}`);
    } finally {
        setLoading(btnCheckStatus, false);
    }
});

// Step 3: Inject Gold
btnInject.addEventListener('click', async () => {
    if (!currentUID) return;

    setLoading(btnInject, true, '⚡ Đang kích hoạt...');
    hideResult(injectResult);

    try {
        const response = await fetch('/api/inject', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': CSRF_TOKEN
            },
            body: JSON.stringify({ uid: currentUID })
        });
        const data = await response.json();

        if (data.success) {
            showResult(injectResult, 'success', `✅ ${data.message}<br>Hết hạn: ${data.expires ? new Date(data.expires).toLocaleString('vi-VN') : 'Không xác định'}`);
            btnInject.classList.add('hidden');
            // Show keep gold section
            showKeepGold();
            updateProgress(4);
        } else {
            showResult(injectResult, 'error', `❌ ${data.message}`);
        }
    } catch (error) {
        showResult(injectResult, 'error', `❌ Lỗi: ${error.message}`);
    } finally {
        setLoading(btnInject, false);
    }
});

// Helper: Show keep gold section
function showKeepGold() {
    keepGoldContent.classList.remove('hidden');
    showResult(keepGoldResult, 'success', '🎉 Kích hoạt thành công! Hãy tải cấu hình để giữ Gold vĩnh viễn.');
}

// Load Config Info
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        configInfo.innerHTML = `
            <div class="config-item">
                <div class="config-label">Tên Cấu Hình</div>
                <div class="config-value">${data.name || 'N/A'}</div>
            </div>
            <div class="config-item">
                <div class="config-label">Sandbox</div>
                <div class="config-value ${data.is_sandbox ? 'active' : 'inactive'}">${data.is_sandbox ? 'Có' : 'Không'}</div>
            </div>
            <div class="config-item">
                <div class="config-label">Fetch Token</div>
                <div class="config-value ${data.has_fetch_token ? 'active' : 'inactive'}">${data.has_fetch_token ? '✓' : '✗'}</div>
            </div>
            <div class="config-item">
                <div class="config-label">App Transaction</div>
                <div class="config-value ${data.has_app_transaction ? 'active' : 'inactive'}">${data.has_app_transaction ? '✓' : '✗'}</div>
            </div>
            <div class="config-item">
                <div class="config-label">Hash Params</div>
                <div class="config-value ${data.has_hash_params ? 'active' : 'inactive'}">${data.has_hash_params ? '✓' : '✗'}</div>
            </div>
            <div class="config-item">
                <div class="config-label">Hash Headers</div>
                <div class="config-value ${data.has_hash_headers ? 'active' : 'inactive'}">${data.has_hash_headers ? '✓' : '✗'}</div>
            </div>
        `;
    } catch (error) {
        configInfo.innerHTML = `<div class="loading">Lỗi: ${error.message}</div>`;
    }
}

// Initialize
loadConfig();