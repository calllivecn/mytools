
 import { http } from './request.js'
 import { initVault } from './vault.js'

const base = document.getElementById('base-url').getAttribute('href');
const baseURL = base.endsWith('/') ? base : base + '/';

const vaultBase = baseURL + 'vault';

// ============ Tab 切换 ============
const tabTotp = document.getElementById('tab-totp');
const tabVault = document.getElementById('tab-vault');
const viewTotp = document.getElementById('view-totp');
const viewVault = document.getElementById('view-vault');

function switch_tab(name){
    const isTotp = name === 'totp';
    viewTotp.hidden = !isTotp;
    viewVault.hidden = isTotp;
    tabTotp.classList.toggle('active', isTotp);
    tabVault.classList.toggle('active', !isTotp);
}

// 依据地址栏 hash(#totp/#vault) 切换视图，两个视图可直接用链接访问
function apply_hash(){
    if (location.hash === '#vault') {
        switch_tab('vault');
    } else {
        switch_tab('totp');
    }
}

window.addEventListener('hashchange', apply_hash);
apply_hash();

// ============ TOTP 视图 ============
const totpLogin = document.getElementById('totp-login');
const totpLoginForm = document.getElementById('totp-login-form');
const totpLoginPassword = document.getElementById('totp-login-password');
const totpLoginMessage = document.getElementById('totp-login-message');
const totpMain = document.getElementById('totp-main');
const totpSearch = document.getElementById('totp-search');
const totpRefresh = document.getElementById('totp-refresh');
const totpAddBtn = document.getElementById('totp-add-btn');
const totpLockBtn = document.getElementById('totp-lock');
const totpTbody = document.getElementById('totp-tbody');

const totpModal = document.getElementById('totp-modal');
const totpForm = document.getElementById('totp-form');
const tfId = document.getElementById('tf-id');
const tfLabel = document.getElementById('tf-label');
const tfSecret = document.getElementById('tf-secret');
const tfNotes = document.getElementById('tf-notes');
const tfSecretInfo = document.getElementById('tf-secret-info');
const tfCancel = document.getElementById('tf-cancel');

const infoModal = document.getElementById('totp-info-modal');
const tiLabel = document.getElementById('ti-label');
const tiNotes = document.getElementById('ti-notes');
const tiSecretInfo = document.getElementById('ti-secret-info');
const tiCopy = document.getElementById('ti-copy');
const tiClose = document.getElementById('ti-close');
let infoEntry = null;

let totpUnlocked = false;
let totpEntries = [];
let totpLoadedAt = 0;
let totpClipboardTimer = null;

function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function totpShowLogin(msg) {
    totpLogin.hidden = false;
    totpMain.hidden = true;
    totpLoginMessage.textContent = msg || '';
}

function totpShowMain() {
    totpLogin.hidden = true;
    totpMain.hidden = false;
}

async function totpLoad() {
    const r = await http.get(baseURL + 'totpall');
    if (r.code !== 0) {
        totpUnlocked = false;
        totpShowLogin(r.msg);
        return;
    }
    totpEntries = r.data || [];
    totpLoadedAt = Date.now();
    totpRender();
}

function totpRender() {
    const q = totpSearch.value.trim().toLowerCase();
    const elapsed = Math.floor((Date.now() - totpLoadedAt) / 1000);

    const filtered = totpEntries.filter(e =>
        !q || String(e.label).toLowerCase().includes(q)
    );

    totpTbody.innerHTML = filtered.map(e => {
        const timeLeft = Math.max(0, e.time_left - elapsed);
        return `
            <tr>
                <td>${esc(e.label)}</td>
                <td>${esc(e.notes)}</td>
                <td class="mono">${e.pw}</td>
                <td>${timeLeft}s</td>
                <td>
                    <button type="button" data-act="copy" data-id="${e.id}">复制</button>
                    ${e.has_info ? '<button type="button" data-act="info" data-id="' + e.id + '">查看</button>' : ''}
                    <button type="button" data-act="edit" data-id="${e.id}">编辑</button>
                    <button type="button" data-act="del" data-id="${e.id}">删除</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function totpCopy(text) {
    try {
        await navigator.clipboard.writeText(text);
        if (totpClipboardTimer) clearTimeout(totpClipboardTimer);
        totpClipboardTimer = setTimeout(() => navigator.clipboard.writeText(''), 15000);
    } catch (e) {
        console.error('复制失败:', e);
    }
}

function totpOpenAdd() {
    tfId.value = '';
    tfLabel.value = '';
    tfSecret.value = '';
    tfSecret.placeholder = 'Base32 密钥';
    tfNotes.value = '';
    tfSecretInfo.value = '';
    totpModal.hidden = false;
    tfLabel.focus();
}

async function totpOpenEdit(entry) {
    const r = await http.get(baseURL + 'totp/get', { id: entry.id });
    if (r.code !== 0) {
        alert(r.msg);
        return;
    }
    const e = r.data;
    tfId.value = e.id;
    tfLabel.value = e.label;
    tfSecret.value = e.secret;
    tfSecret.placeholder = 'Base32 密钥';
    tfNotes.value = e.notes || '';
    tfSecretInfo.value = e.secret_info || '';
    totpModal.hidden = false;
    tfLabel.focus();
}

async function totpOpenInfo(entry) {
    const r = await http.get(baseURL + 'totp/get', { id: entry.id });
    if (r.code !== 0) {
        alert(r.msg);
        return;
    }
    infoEntry = r.data;
    tiLabel.textContent = infoEntry.label;
    tiNotes.textContent = infoEntry.notes || '（无）';
    tiSecretInfo.textContent = infoEntry.secret_info || '（无）';
    infoModal.hidden = false;
}

totpTbody.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('button');
    if (!btn) return;
    const id = btn.dataset.id;
    const act = btn.dataset.act;
    const entry = totpEntries.find(e => e.id === id);
    if (!entry) return;

    if (act === 'copy') {
        await totpCopy(entry.pw);
    } else if (act === 'info') {
        await totpOpenInfo(entry);
    } else if (act === 'edit') {
        await totpOpenEdit(entry);
    } else if (act === 'del') {
        if (!confirm(`确认删除 ${entry.label} ？`)) return;
        const r = await http.post(baseURL + 'totp/delete', { id });
        if (r.code === 0) await totpLoad();
        else alert(r.msg);
    }
});

totpLoginForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const r = await http.post(baseURL + 'login', { password: totpLoginPassword.value });
    totpLoginPassword.value = '';
    if (r.code === 0) {
        totpUnlocked = true;
        totpShowMain();
        await totpLoad();
    } else {
        totpLoginMessage.textContent = r.msg;
    }
});

totpRefresh.addEventListener('click', totpLoad);
totpAddBtn.addEventListener('click', totpOpenAdd);
totpSearch.addEventListener('input', totpRender);

totpLockBtn.addEventListener('click', async () => {
    await http.post(baseURL + 'logout');
    totpUnlocked = false;
    totpEntries = [];
    totpShowLogin('已锁定');
});

totpForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const data = {
        label: tfLabel.value,
        secret: tfSecret.value,
        notes: tfNotes.value,
        secret_info: tfSecretInfo.value,
    };
    const id = tfId.value;
    const r = id
        ? await http.put(baseURL + 'totp/update', { ...data, id })
        : await http.post(baseURL + 'totp/add', data);
    if (r.code === 0) {
        totpModal.hidden = true;
        await totpLoad();
    } else {
        alert(r.msg);
    }
});

tfCancel.addEventListener('click', () => { totpModal.hidden = true; });
tiClose.addEventListener('click', () => { infoModal.hidden = true; });
tiCopy.addEventListener('click', async () => {
    if (infoEntry) await totpCopy(infoEntry.secret_info || '');
});

// 每秒刷新倒计时，到期或超时则重新拉取动态密码
setInterval(() => {
    if (!totpUnlocked || totpLoadedAt === 0) return;
    const now = Date.now();
    const elapsed = Math.floor((now - totpLoadedAt) / 1000);
    const expired = totpEntries.some(e => (e.time_left - elapsed) <= 0);
    if (expired || (now - totpLoadedAt >= 30000)) {
        totpLoad();
    } else {
        totpRender();
    }
}, 1000);

const totp_status = await http.get(baseURL + 'login');
if (totp_status.code === 0) {
    totpUnlocked = true;
    totpShowMain();
    await totpLoad();
} else {
    totpShowLogin();
}

// ============ 密码库视图 ============
initVault(vaultBase);
