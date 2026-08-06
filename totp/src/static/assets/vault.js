import { http } from './request.js';

const MASK = '••••••••';

const PW_SETS = [
    'abcdefghijklmnopqrstuvwxyz',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '0123456789',
    '!@#$%^&*()_+-=[]{}|;:,.<>?',
];
const PW_ALL = PW_SETS.join('');

function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function randInt(n) {
    const buf = new Uint32Array(1);
    crypto.getRandomValues(buf);
    return buf[0] % n;
}

function genPassword(len = 16) {
    const arr = PW_SETS.map(s => s[randInt(s.length)]);
    while (arr.length < len) {
        arr.push(PW_ALL[randInt(PW_ALL.length)]);
    }
    for (let i = arr.length - 1; i > 0; i--) {
        const j = randInt(i + 1);
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr.join('');
}

export async function initVault(vaultBase) {

    const loginBox = document.getElementById('vault-login');
    const mainBox = document.getElementById('vault-main');
    const loginForm = document.getElementById('vault-login-form');
    const loginPassword = document.getElementById('vault-password');
    const loginPassword2 = document.getElementById('vault-password2');
    const loginPassword3 = document.getElementById('vault-password3');
    const loginMessage = document.getElementById('vault-login-message');
    const initHint = document.getElementById('vault-init-hint');
    const confirmField = document.getElementById('vault-confirm-field');
    const loginSubmit = document.getElementById('vault-login-submit');
    let initialized = false;

    const searchInput = document.getElementById('vault-search');
    const refreshBtn = document.getElementById('vault-refresh');
    const addBtn = document.getElementById('vault-add-btn');
    const lockBtn = document.getElementById('vault-lock');
    const chpwBtn = document.getElementById('vault-chpw-btn');
    const tbody = document.getElementById('vault-tbody');

    const modal = document.getElementById('vault-modal');
    const vaultForm = document.getElementById('vault-form');
    const vfId = document.getElementById('vf-id');
    const vfSite = document.getElementById('vf-site');
    const vfUsername = document.getElementById('vf-username');
    const vfPassword = document.getElementById('vf-password');
    const vfGen = document.getElementById('vf-gen');
    const vfCategory = document.getElementById('vf-category');
    const vfNotes = document.getElementById('vf-notes');
    const vfCancel = document.getElementById('vf-cancel');

    const pwModal = document.getElementById('vault-pw-modal');
    const vpwForm = document.getElementById('vault-pw-form');
    const vpwOld = document.getElementById('vpw-old');
    const vpwNew = document.getElementById('vpw-new');
    const vpwConfirm = document.getElementById('vpw-confirm');
    const vpwCancel = document.getElementById('vpw-cancel');

    let entries = [];
    const revealed = new Set();
    const pwCache = new Map();
    let clipboardTimer = null;

    function showLogin(msg) {
        loginBox.hidden = false;
        mainBox.hidden = true;
        loginMessage.textContent = msg || '';
        if (initialized) {
            initHint.style.display = 'none';
            confirmField.hidden = true;
            loginSubmit.textContent = '解锁';
        } else {
            initHint.style.display = 'block';
            confirmField.hidden = false;
            loginSubmit.textContent = '创建密码';
        }
    }

    function showMain() {
        loginBox.hidden = true;
        mainBox.hidden = false;
    }

    async function loadEntries() {
        const q = searchInput.value.trim();
        const r = q
            ? await http.get(vaultBase + '/search', { q })
            : await http.get(vaultBase + '/list');
        if (r.code !== 0) {
            showLogin(r.msg);
            return;
        }
        entries = r.data || [];
        entries.forEach(e => {
            if (e.password !== undefined) pwCache.set(e.id, e.password);
        });
        renderTable();
    }

    function renderTable() {
        tbody.innerHTML = entries.map(e => {
            const shown = revealed.has(e.id) ? (pwCache.get(e.id) || '') : MASK;
            return `
            <tr>
                <td>${esc(e.site)}</td>
                <td>${esc(e.username)}</td>
                <td class="mono">
                    <span data-id="${e.id}">${shown}</span>
                    <button type="button" data-act="toggle" data-id="${e.id}">${revealed.has(e.id) ? '隐藏' : '显示'}</button>
                    <button type="button" data-act="copy" data-id="${e.id}">复制</button>
                </td>
                <td>${esc(e.category)}</td>
                <td>
                    <button type="button" data-act="edit" data-id="${e.id}">编辑</button>
                    <button type="button" data-act="del" data-id="${e.id}">删除</button>
                </td>
            </tr>
        `;
        }).join('');
    }

    async function getPassword(id) {
        if (pwCache.has(id)) return pwCache.get(id);
        const r = await http.get(vaultBase + '/get', { id });
        if (r.code !== 0) throw new Error(r.msg);
        pwCache.set(id, r.data.password);
        return r.data.password;
    }

    async function copyPassword(text) {
        try {
            await navigator.clipboard.writeText(text);
            if (clipboardTimer) clearTimeout(clipboardTimer);
            clipboardTimer = setTimeout(() => navigator.clipboard.writeText(''), 15000);
        } catch (e) {
            console.error('复制失败:', e);
        }
    }

    function openModal(id, entry) {
        vfId.value = id || '';
        vfSite.value = entry.site || '';
        vfUsername.value = entry.username || '';
        vfPassword.value = entry.password || '';
        vfCategory.value = entry.category || '';
        vfNotes.value = entry.notes || '';
        modal.hidden = false;
        vfSite.focus();
    }

    tbody.addEventListener('click', async (ev) => {
        const btn = ev.target.closest('button');
        if (!btn) return;
        const id = btn.dataset.id;
        const act = btn.dataset.act;
        const entry = entries.find(e => e.id === id);
        if (!entry) return;

        if (act === 'toggle') {
            if (revealed.has(id)) {
                revealed.delete(id);
                btn.textContent = '显示';
                btn.parentElement.querySelector('span').textContent = MASK;
            } else {
                try {
                    const pw = await getPassword(id);
                    revealed.add(id);
                    btn.textContent = '隐藏';
                    btn.parentElement.querySelector('span').textContent = pw;
                } catch (e) {
                    alert(e.message);
                }
            }
        } else if (act === 'copy') {
            try {
                await copyPassword(await getPassword(id));
            } catch (e) {
                alert(e.message);
            }
        } else if (act === 'edit') {
            let pw = '';
            try {
                pw = await getPassword(id);
            } catch (e) { /* 保留空值 */ }
            openModal(id, { ...entry, password: pw });
        } else if (act === 'del') {
            if (!confirm(`确认删除 ${entry.site || '(无站点)'} ？`)) return;
            const r = await http.post(vaultBase + '/delete', { id });
            if (r.code === 0) await loadEntries();
            else alert(r.msg);
        }
    });

    loginForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const pw = loginPassword.value;
        let r;
        if (!initialized) {
            if (pw !== loginPassword2.value || pw !== loginPassword3.value) {
                loginMessage.textContent = '三次输入的密码不一致';
                return;
            }
            r = await http.post(vaultBase + '/init', { password: pw });
        } else {
            r = await http.post(vaultBase + '/login', { password: pw });
        }
        loginPassword.value = loginPassword2.value = loginPassword3.value = '';
        if (r.code === 0) {
            initialized = true;
            showMain();
            await loadEntries();
        } else {
            loginMessage.textContent = r.msg;
        }
    });

    lockBtn.addEventListener('click', async () => {
        await http.post(vaultBase + '/logout');
        revealed.clear();
        pwCache.clear();
        showLogin('已锁定');
    });

    refreshBtn.addEventListener('click', loadEntries);
    addBtn.addEventListener('click', () => openModal(null, {}));

    let searchTimer = null;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadEntries, 300);
    });

    vaultForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const data = {
            site: vfSite.value,
            username: vfUsername.value,
            password: vfPassword.value,
            category: vfCategory.value,
            notes: vfNotes.value,
        };
        const id = vfId.value;
        const r = id
            ? await http.put(vaultBase + '/update', { ...data, id })
            : await http.post(vaultBase + '/add', data);
        if (r.code === 0) {
            modal.hidden = true;
            await loadEntries();
        } else {
            alert(r.msg);
        }
    });

    vfCancel.addEventListener('click', () => { modal.hidden = true; });
    vfGen.addEventListener('click', () => { vfPassword.value = genPassword(16); });

    chpwBtn.addEventListener('click', () => {
        vpwOld.value = vpwNew.value = vpwConfirm.value = '';
        pwModal.hidden = false;
    });

    vpwCancel.addEventListener('click', () => { pwModal.hidden = true; });

    vpwForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        if (vpwNew.value !== vpwConfirm.value) {
            alert('两次输入的新密码不一致');
            return;
        }
        const r = await http.post(vaultBase + '/password', {
            old_password: vpwOld.value,
            new_password: vpwNew.value,
        });
        if (r.code === 0) {
            pwModal.hidden = true;
            alert('主密码已修改');
        } else {
            alert(r.msg);
        }
    });

    const r = await http.get(vaultBase + '/status');
    if (r.code === 0 && r.unlocked) {
        initialized = true;
        showMain();
        await loadEntries();
    } else {
        initialized = r.initialized === true;
        showLogin();
    }
}
