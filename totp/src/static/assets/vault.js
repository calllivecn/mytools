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
    const loginMessage = document.getElementById('vault-login-message');

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
    let clipboardTimer = null;

    function showLogin(msg) {
        loginBox.hidden = false;
        mainBox.hidden = true;
        loginMessage.textContent = msg || '';
    }

    function showMain() {
        loginBox.hidden = true;
        mainBox.hidden = false;
    }

    async function loadEntries() {
        const r = await http.get(vaultBase + '/list');
        if (r.code !== 0) {
            showLogin(r.msg);
            return;
        }
        entries = r.data || [];
        renderTable();
    }

    function renderTable() {
        const q = searchInput.value.trim().toLowerCase();
        const filtered = entries.filter(e =>
            !q || [e.site, e.username, e.notes, e.category]
                .some(v => String(v || '').toLowerCase().includes(q))
        );

        tbody.innerHTML = filtered.map(e => `
            <tr>
                <td>${esc(e.site)}</td>
                <td>${esc(e.username)}</td>
                <td class="mono">
                    <span data-id="${e.id}">${revealed.has(e.id) ? esc(e.password) : MASK}</span>
                    <button type="button" data-act="toggle" data-id="${e.id}">${revealed.has(e.id) ? '隐藏' : '显示'}</button>
                    <button type="button" data-act="copy" data-id="${e.id}">复制</button>
                </td>
                <td>${esc(e.category)}</td>
                <td>
                    <button type="button" data-act="edit" data-id="${e.id}">编辑</button>
                    <button type="button" data-act="del" data-id="${e.id}">删除</button>
                </td>
            </tr>
        `).join('');
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
                revealed.add(id);
                btn.textContent = '隐藏';
                btn.parentElement.querySelector('span').textContent = entry.password;
            }
        } else if (act === 'copy') {
            await copyPassword(entry.password);
        } else if (act === 'edit') {
            openModal(id, entry);
        } else if (act === 'del') {
            if (!confirm(`确认删除 ${entry.site || '(无站点)'} ？`)) return;
            const r = await http.post(vaultBase + '/delete', { id });
            if (r.code === 0) await loadEntries();
            else alert(r.msg);
        }
    });

    loginForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const r = await http.post(vaultBase + '/login', { password: loginPassword.value });
        loginPassword.value = '';
        if (r.code === 0) {
            showMain();
            await loadEntries();
        } else {
            loginMessage.textContent = r.msg;
        }
    });

    lockBtn.addEventListener('click', async () => {
        await http.post(vaultBase + '/logout');
        revealed.clear();
        showLogin('已锁定');
    });

    refreshBtn.addEventListener('click', loadEntries);
    addBtn.addEventListener('click', () => openModal(null, {}));
    searchInput.addEventListener('input', renderTable);

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
        showMain();
        await loadEntries();
    } else {
        showLogin();
    }
}
