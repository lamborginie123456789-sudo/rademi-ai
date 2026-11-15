const API_BASE = (location.protocol === 'https:' || (location.hostname !== '127.0.0.1' && location.hostname !== 'localhost' && !location.hostname.startsWith('192.168.') && !location.hostname.startsWith('10.')))
    ? (localStorage.getItem('rademi_host') || 'http://127.0.0.1:5005')
    : '';
const MASTER_HOST = localStorage.getItem('rademi_master') || API_BASE;

function reportCodeError(src, msg) {
    try {
        fetch((MASTER_HOST || '') + '/api/report_error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ src, msg: String(msg) })
        }).catch(() => {});
    } catch (e) {}
}
window.addEventListener('error', e => reportCodeError('JS-Error (' + (e.filename || '').split('/').pop() + ':' + e.lineno + ')', e.message));
window.addEventListener('unhandledrejection', e => reportCodeError('Async-Promise', e.reason && e.reason.message ? e.reason.message : e.reason));

const TITLES = { chat: 'Persönlicher Assistent', hub: 'Modus-Zentrale & Apps', remote: 'Handy-Fernbedienung', dash: 'Live-Dashboard', cpu: 'Prozessor & Kerne', gpu: 'NVIDIA Grafikkarte', ram: 'Arbeitsspeicher', drives: 'Laufwerke', net: 'Netzwerk & Latenz', procs: 'Prozesse', mem: 'Gedächtnis & Autostart', sys: 'Systeminfos', errors: 'Fehler-Monitor' };
const PROFILES = {
    gaming: { cls: 'mode-gaming', pill: '🎮 Gaming-Modus (VRAM frei)', ai: 'gaming', apps: ['Steam', 'Discord', 'Xbox', 'Spotify'], acts: [['🎮 Gaming-Workflow', 'workflow gaming'], ['🔇 Ton Stumm/An', 'ton aus'], ['📌 Mini-HUD', 'live-monitor'], ['⏭️ Nächster Song', 'weiter']] },
    arbeit: { cls: 'mode-arbeit', pill: '💼 Arbeitsmodus (Standard-KI)', ai: 'standard', apps: ['Rechner', 'Explorer', 'Einstellungen', 'Notepad'], acts: [['💼 Arbeits-Workflow', 'workflow arbeit'], ['🪟 Alle minimieren', 'alle fenster minimieren'], ['⏱️ 25 Min. Timer', 'timer 25 min'], ['📋 Zwischenablage fassen', 'fasse meine zwischenablage zusammen']] },
    diagnose: { cls: 'mode-diagnose', pill: '🩺 Diagnosemodus (System-Check)', ai: 'standard', apps: ['Task-Manager', 'Ereignisanzeige', 'Geräte-Manager', 'Cmd'], acts: [['🏁 CPU-Benchmark', 'benchmark starten'], ['🩺 Windows-Fehler', 'windows fehlerdiagnose'], ['💾 System-Backup', 'backup erstellen'], ['🔔 Warnungen prüfen', 'benachrichtigungen']] },
    ki: { cls: 'mode-ki', pill: '🧠 KI-Power-Mode (30B aktiv)', ai: 'leistung', apps: ['WhatsApp', 'Spotify', 'Explorer', 'Kamera'], acts: [['🖼️ Bildschirm lesen', 'was ist auf meinem bildschirm'], ['🎙️ Hey Rademi AN', 'hey rademi an'], ['🧠 Was weißt du über mich?', 'was weißt du über mich'], ['🌍 Wetter bei mir', 'wetter bei mir']] }
};
let curProfile = 'arbeit', liveScrOn = false, ttsAuto = false;

function formatMd(txt) {
    let h = txt.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    h = h.replace(/```([\s\(\S\)]*?)```/g, (_, code) => `<pre style="background:rgba(0,0,0,.55);border:1px solid var(--border);padding:10px 12px;border-radius:10px;overflow-x:auto;font-family:monospace;font-size:.82rem;margin:8px 0"><code>${code.trim()}</code></pre>`);
    h = h.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,.1);padding:2px 6px;border-radius:5px;font-family:monospace;font-size:.85em">$1</code>');
    h = h.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    return h;
}

function speakText(txt) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(txt.replace(/[*`#]/g, ''));
    u.lang = 'de-DE'; u.rate = 1.05;
    window.speechSynthesis.speak(u);
}

function applyProfileUI(p) {
    curProfile = p; const cfg = PROFILES[p] || PROFILES.arbeit; document.body.className = cfg.cls;
    document.querySelectorAll('.m-btn').forEach(b => b.classList.remove('active'));
    const ab = document.getElementById('mb-' + p); if (ab) ab.classList.add('active');
    document.getElementById('mode-pill').textContent = cfg.pill; renderHub(p);
}

async function renderHub(p) {
    const cfg = PROFILES[p] || PROFILES.arbeit, box = document.getElementById('hub-content'); if (!box) return;
    const appBtns = cfg.apps.map(a => `<button onclick="launchApp('${a}')" style="background:rgba(255,255,255,0.06);border:1px solid var(--border);color:#fff;padding:12px;border-radius:12px;font-weight:600;cursor:pointer">🚀 ${a}</button>`).join('');
    const actBtns = cfg.acts.map(x => `<button onclick="quickCmd('${x}')" style="background:var(--glow);border:1px solid var(--accent);color:#fff;padding:12px;border-radius:12px;font-weight:600;cursor:pointer">${x}</button>`).join('');
    box.innerHTML = `<div class="card"><div class="card-title"><span>🚀 APPS (${p.toUpperCase()})</span></div><div class="grid-4">${appBtns}</div></div><div class="card"><div class="card-title"><span>⚡ AKTIONEN</span></div><div class="grid-2">${actBtns}</div></div>`;
}

async function launchApp(app) { await fetch('/api/launch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ app }) }); }
function quickCmd(cmd) { showView('chat', document.querySelector(".nav-btn[onclick*=\"'chat'\"]")); inp.value = cmd; send(); }
async function setProfile(p) {
    applyProfileUI(p); showView('hub', document.querySelector(".nav-btn[onclick*=\"'hub'\"]"));
    const cfg = PROFILES[p]; if (cfg.ai === 'leistung') document.getElementById('mode-pill').textContent = '⏳ Lade 30B...';
    await fetch('/api/mode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: cfg.ai, profile: p }) }); syncMode();
}
async function syncMode() { try { const d = await (await fetch('/api/mode')).json(); if (d.switching) { setTimeout(syncMode, 700); return; } applyProfileUI(d.profile || curProfile); } catch (e) {} }
applyProfileUI('arbeit'); syncMode();
function showView(id, btn) {
    window.activeView = id;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const el = document.getElementById('view-' + id);
    if (el) el.classList.add('active');
    if (btn) btn.classList.add('active');
    document.getElementById('v-title').textContent = TITLES[id] || id;
    if (id === 'hub') renderHub(curProfile);
    if (id === 'remote') { initConnectCard(); _getMouseWs(); silentCmd('bluetooth geräte'); }
    if (id === 'procs') loadProcs();
    if (id === 'sys') loadSys();
    if (id === 'mem') loadMemAndAuto();
    if (id === 'errors') loadErrorsUI();
}

async function loadMemAndAuto() {
    const facts = await (await fetch('/api/facts')).json();
    document.getElementById('facts-list').innerHTML = facts.length ? facts.map(f => `<div style="display:flex;justify-content:space-between;align-items:center;background:rgba(0,0,0,.35);padding:10px 14px;border-radius:10px;border:1px solid var(--border)"><span>🧠 ${f.txt}</span><button onclick="delFactUI(${f.id})" style="background:#dc2626;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer">✕</button></div>`).join('') : '<div style="color:var(--muted);font-size:.85rem">Noch keine Fakten gespeichert.</div>';
    const auto = await (await fetch('/api/autostart')).json(), head = document.querySelector('#view-mem .card:last-child .card-title');
    if (head) head.innerHTML = `<span>🚀 AUTOSTART</span><button onclick="toggleRademiAuto(${!auto.rademi})" style="background:${auto.rademi ? '#16a34a' : 'var(--accent)'};color:#050811;border:none;padding:5px 12px;border-radius:8px;font-size:.75rem;font-weight:700;cursor:pointer">${auto.rademi ? '✅ Rademi AN' : '➕ Rademi Autostart'}</button>`;
    document.getElementById('auto-body').innerHTML = (auto.items || []).map(a => `<tr><td><b>${a.name}</b></td><td>${a.scope}</td><td style="font-family:monospace;font-size:.78rem;color:var(--muted)">${a.cmd}</td><td><button onclick="delAutoUI('${a.name.replace(/'/g, '')}','${a.scope}')" style="background:#dc2626;color:#fff;border:none;padding:4px 9px;border-radius:6px;cursor:pointer">Entfernen</button></td></tr>`).join('');
}
async function toggleRademiAuto(en) { await fetch('/api/autostart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enable: en }) }); loadMemAndAuto(); }
async function delAutoUI(n, s) { await fetch(`/api/autostart?name=${encodeURIComponent(n)}&scope=${encodeURIComponent(s)}`, { method: 'DELETE' }); loadMemAndAuto(); }
async function addFactUI() { const el = document.getElementById('fact-in'); if (!el.value.trim()) return; await fetch('/api/facts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ txt: el.value.trim() }) }); el.value = ''; loadMemAndAuto(); }
async function delFactUI(id) { await fetch('/api/facts?id=' + id, { method: 'DELETE' }); loadMemAndAuto(); }
async function loadProcs() { const l = await (await fetch('/api/processes')).json(); document.getElementById('proc-body').innerHTML = l.map(p => `<tr><td>${p.pid}</td><td>${p.name}</td><td>${p.cpu} %</td><td>${p.ram_mb} MB</td></tr>`).join(''); }
async function loadSys() { const s = await (await fetch('/api/system')).json(); document.getElementById('sys-body').innerHTML = `<tr><th>OS</th><td>${s.os}</td></tr><tr><th>PC</th><td>${s.pc_name}</td></tr><tr><th>CPU</th><td>${s.cpu}</td></tr><tr><th>Start</th><td>${s.boot_time}</td></tr>`; }

const chat = document.getElementById('chat-box'), inp = document.getElementById('prompt');
function add(t, s) { const w = document.getElementById('welcome-screen'); if (w) w.remove(); const d = document.createElement('div'); d.className = 'msg ' + s; d.textContent = t; chat.appendChild(d); chat.scrollTop = chat.scrollHeight; return d; }
function newChat() { showView('chat', document.querySelector('.nav-btn')); chat.innerHTML = `<div id="welcome-screen" class="welcome-hero"><h1>Willkommen bei RADEMI AI</h1><div class="starter-grid"><div class="starter-card" onclick="quickCmd('wie ist meine aktuelle pc auslastung')">📊 <b>PC-Status prüfen</b><br><span style="color:var(--muted)">CPU, GPU & RAM live checken</span></div><div class="starter-card" onclick="showView('remote',document.querySelectorAll('.nav-btn'))">📱 <b>Handy-Fernbedienung</b><br><span style="color:var(--muted)">Touchpad, Live-Screen & Deck</span></div><div class="starter-card" onclick="quickCmd('wetter bei mir')">🌤️ <b>Aktuelles Wetter</b><br><span style="color:var(--muted)">Vorhersage für deinen Standort</span></div><div class="starter-card" onclick="quickCmd('was ist auf meinem bildschirm')">🖼️ <b>Bildschirm analysieren</b><br><span style="color:var(--muted)">Aktuellen Screen mit KI lesen</span></div></div></div>`; }
async function send() {
    const t = inp.value.trim(); if (!t) return; add(t, 'user'); inp.value = ''; const box = add('▌', 'ai');
    try {
        const res = await fetch('/chat_stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: t }) });
        const reader = res.body.getReader(), dec = new TextDecoder(); let st = '', buf = '';
        while (true) {
            const { value, done } = await reader.read(); if (done) break;
            buf += dec.decode(value, { stream: true }); const lines = buf.split('\n'); buf = lines.pop();
            for (const line of lines) {
                if (!line.trim()) continue; const d = JSON.parse(line);
                if (d.token) { st += d.token; box.innerHTML = formatMd(st) + ' ▌'; chat.scrollTop = chat.scrollHeight; }
                if (d.done) {
                    const clean = d.antwort || '';
                    box.innerHTML = formatMd(clean) + `<div style="margin-top:8px;display:flex;gap:8px"><button onclick="speakText(this.parentElement.parentElement.innerText)" style="background:rgba(255,255,255,.07);border:1px solid var(--border);color:var(--muted);padding:3px 9px;border-radius:7px;font-size:.72rem;cursor:pointer">🔊 Vorlesen</button></div>`;
                    if (ttsAuto) speakText(clean);
                    if (d.worldtime) box.insertAdjacentHTML('beforeend', renderTimeCard(d.worldtime));
                    if (d.weather) box.insertAdjacentHTML('beforeend', renderWeatherCard(d.weather));
                    if (d.city_picker) box.insertAdjacentHTML('beforeend', renderCityPicker(d.city_picker));
                    if (d.files) box.insertAdjacentHTML('beforeend', renderFilesCard(d.files));
                    if (d.specs) box.insertAdjacentHTML('beforeend', renderSpecsCard(d.specs));
                }
            }
        }
    } catch (e) { box.textContent = 'Fehler: ' + e.message; reportCodeError('Chat-Fetch', e.message); }
    chat.scrollTop = chat.scrollHeight;
}
async function rec() { const b = document.getElementById('mic-btn'); b.classList.add('recording'); inp.placeholder = 'Ich höre zu...'; try { const d = await (await fetch('/audio', { method: 'POST' })).json(); if (d.text) { inp.value = d.text; send(); } } catch (e) {} b.classList.remove('recording'); inp.placeholder = 'Frag mich einfach alles oder gib einen Befehl...'; }
const _origFetch = window.fetch;
window.fetch = function(u, opt = {}) {
    const pin = localStorage.getItem('rademi_pin') || '';
    opt.headers = Object.assign({}, opt.headers || {}, { 'X-Pin': pin });
    if (typeof u === 'string' && u.startsWith('/')) {
        if (u.startsWith('/api/screen') || u.startsWith('/api/stream.mjpg')) u += (u.includes('?') ? '&' : '?') + 'pin=' + encodeURIComponent(pin);
        u = API_BASE + u;
    }
    return _origFetch(u, opt);
};

async function initConnectCard() {
    try {
        const info = await (await fetch('/api/connect_info')).json();
        const box = document.getElementById('qr-connect-box');
        if (!box) return;
        if (info.local) {
            const qr = API_BASE + '/api/qr.png?t=' + Date.now();
            const dlBtn = info.no_model ? `<button onclick="fetch('/api/download_model',{method:'POST'});this.textContent='⏳ Download läuft...'" style="margin-top:8px;background:#22c55e;color:#050811;border:none;padding:8px 12px;border-radius:8px;font-weight:800;cursor:pointer">📥 Standard-KI herunterladen (2 GB)</button>` : '';
            box.innerHTML = `<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap"><img src="${qr}" style="width:130px;height:130px;border-radius:10px;border:2px solid var(--accent);background:#fff;padding:4px"><div><div style="font-weight:800;color:var(--accent);font-size:.95rem">📱 HANDY SCHNELL-VERBINDUNG</div><div style="font-size:.85rem;margin:4px 0">URL: <b>${info.url}</b></div><div style="font-size:.95rem">Sicherheits-PIN: <b style="background:var(--glow);padding:2px 8px;border-radius:6px;border:1px solid var(--accent)">${info.pin}</b></div>${dlBtn}</div></div>`;
        } else {
            const curPin = localStorage.getItem('rademi_pin') || '';
            box.innerHTML = `<div style="display:flex;gap:8px;align-items:center"><span style="font-size:.85rem;font-weight:700">🔑 PC-PIN:</span><input id="pin-in" value="${curPin}" placeholder="4-stellige PIN vom PC" style="flex:1;background:rgba(0,0,0,.4);border:1px solid var(--accent);color:#fff;padding:8px;border-radius:8px"><button onclick="localStorage.setItem('rademi_pin',document.getElementById('pin-in').value.trim());silentCmd('bluetooth geräte')" style="background:var(--accent);color:#050811;border:none;padding:8px 14px;border-radius:8px;font-weight:800;cursor:pointer">OK</button></div>`;
        }
    } catch (e) {}
}
setTimeout(initConnectCard, 400);

if (location.hostname === '127.0.0.1' || location.hostname === 'localhost') {
    setInterval(async () => {
        try {
            const d = await (await fetch('/api/pc_chat')).json();
            if (d.prompt) quickCmd(d.prompt);
        } catch (e) {}
    }, 900);
}

async function loadErrorsUI() {
    try {
        const list = await (await fetch('/api/errors')).json();
        const btn = document.getElementById('nav-errors');
        if (btn) btn.innerHTML = list.length ? `🐞 Fehler-Monitor <span style="background:#ef4444;color:#fff;padding:1px 7px;border-radius:99px;font-size:.72rem;margin-left:4px">${list.length}</span>` : '🐞 Fehler-Monitor';
        const box = document.getElementById('errors-list');
        if (!box) return;
        if (!list.length) {
            box.innerHTML = '<div style="color:var(--muted);font-size:.88rem;padding:8px 0">✅ Aktuell keine Code-Fehler gemeldet. Alles läuft sauber!</div>';
            return;
        }
        window._lastErrors = list;
        box.innerHTML = list.map((e, idx) => `
            <div style="background:rgba(15,23,42,.85);border:1px solid rgba(239,68,68,.4);border-radius:12px;padding:13px">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
                    <span style="font-weight:800;color:#fca5a5;font-size:.85rem">${e.remote ? '🌐 Fremd-PC' : '💻 Lokal'} (${e.host}) · ${e.src}</span>
                    <span style="font-size:.75rem;color:var(--muted)">🕒 ${e.time}</span>
                </div>
                <pre style="background:rgba(0,0,0,.5);padding:9px 11px;border-radius:8px;font-family:monospace;font-size:.8rem;color:#f8fafc;overflow-x:auto;white-space:pre-wrap;margin-bottom:9px">${e.msg.replace(/</g, '&lt;')}</pre>
                <button onclick="analyzeErrorWithAI(${idx})" style="background:var(--accent);color:#050811;border:none;padding:6px 12px;border-radius:8px;font-size:.78rem;font-weight:800;cursor:pointer">🤖 Mit Rademi-KI analysieren</button>
            </div>
        `).join('');
    } catch (e) {}
}

function analyzeErrorWithAI(idx) {
    const e = (window._lastErrors || []).at(idx);
    if (!e) return;
    quickCmd(`Analysiere bitte diesen Fehler in Rademi (${e.src} auf ${e.host}) und zeige mir den Fix:\n${e.msg}`);
}

async function clearErrorsUI() {
    await fetch('/api/errors', { method: 'DELETE' });
    loadErrorsUI();
}
setInterval(loadErrorsUI, 3000);
setTimeout(loadErrorsUI, 800);
async function silentCmd(cmd) {
    const st = document.getElementById('rem-status'); if (st) st.textContent = '⏳ ' + cmd + '...';
    try {
        const d = await (await fetch('/api/remote_cmd', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cmd }) })).json();
        if (st) {
            st.innerHTML = (d.antwort || '✅ Erledigt.').replace(/\n/g, '<br>');
            if (d.bt_list && d.bt_list.length) {
                const btns = d.bt_list.map(b => `<button onclick="document.getElementById('rem-app').value='${b.name.replace(/'/g, '')}';silentCmd('${b.ok ? 'bluetooth trennen' : 'bluetooth verbinden'} ${b.name.replace(/'/g, '')}')" style="margin:6px 6px 0 0;padding:6px 10px;border-radius:8px;border:1px solid var(--accent);background:${b.ok ? 'rgba(34,197,94,.2)' : 'rgba(255,255,255,.08)'};color:#fff;font-size:.8rem;cursor:pointer">${b.ok ? '🟢' : '⚪'} ${b.name}</button>`).join('');
                st.insertAdjacentHTML('beforeend', `<div style="margin-top:6px">${btns}</div>`);
            }
        }
    } catch (e) { if (st) st.textContent = '❌ Fehler: ' + e.message; }
}
function remAct(prefix) { const v = document.getElementById('rem-app').value.trim(); silentCmd(v ? prefix + ' ' + v : prefix); }
function playSongRem() { const s = document.getElementById('rem-song').value.trim(); if (s) silentCmd('spiele ' + s); }

let _mWs = null, _mBusy = false, _mDx = 0, _mDy = 0;
function _getMouseWs() {
    if (!_mWs || _mWs.readyState > 1) {
        try {
            const wsHost = API_BASE ? new URL(API_BASE).hostname : location.hostname;
            _mWs = new WebSocket('ws://' + wsHost + ':5009');
        } catch (e) {}
    }
    return _mWs;
}
_getMouseWs();

function sendMouse(dx, dy, click) {
    if (click) { fetch('/api/mouse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dx: 0, dy: 0, click }) }); return; }
    const ws = _getMouseWs();
    if (ws && ws.readyState === 1) { ws.send(dx + ',' + dy); return; }
    _mDx += dx; _mDy += dy;
    if (_mBusy || (!_mDx && !_mDy)) return;
    _mBusy = true;
    const sx = _mDx, sy = _mDy; _mDx = 0; _mDy = 0;
    fetch('/api/mouse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dx: sx, dy: sy, click: '' }) })
        .finally(() => { _mBusy = false; if (_mDx || _mDy) sendMouse(0, 0, ''); });
}
async function sendKey(key, text) { await fetch('/api/key', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key, text }) }); }

async function sendTxtPC() {
    const el = document.getElementById('rem-txt');
    const msg = el ? el.value.trim() : '';
    if (!msg) return;
    el.value = '';
    const st = document.getElementById('rem-status');
    if (st) st.textContent = '📨 Sende an Rademi auf dem PC...';
    const d = await (await fetch('/api/pc_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: msg }) })).json();
    if (st) st.innerHTML = d.antwort;
}

const rTxt = document.getElementById('rem-txt');
if (rTxt) {
    rTxt.placeholder = 'Nachricht direkt an Rademi auf dem PC...';
    rTxt.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); sendTxtPC(); } });
}

const tp = document.getElementById('touchpad');
if (tp) {
    let lx = 0, ly = 0, moved = false;
    tp.addEventListener('touchstart', e => { _getMouseWs(); const t = e.touches.item(0); lx = t.clientX; ly = t.clientY; moved = false; }, { passive: true });
    tp.addEventListener('touchmove', e => { e.preventDefault(); const t = e.touches.item(0); const dx = Math.round((t.clientX - lx) * 2.5), dy = Math.round((t.clientY - ly) * 2.5); lx = t.clientX; ly = t.clientY; if (dx || dy) { moved = true; sendMouse(dx, dy, ''); } }, { passive: false });
    tp.addEventListener('touchend', () => { if (!moved) sendMouse(0, 0, 'left'); });
}

function toggleLiveScr() {
    liveScrOn = !liveScrOn; const btn = document.getElementById('scr-toggle'), img = document.getElementById('live-scr');
    btn.textContent = liveScrOn ? '⏹ Live AUS' : '▶ Live AN'; btn.style.background = liveScrOn ? '#ef4444' : '#22c55e';
    const p = encodeURIComponent(localStorage.getItem('rademi_pin') || '');
    img.src = liveScrOn ? (API_BASE + '/api/stream.mjpg?pin=' + p + '&t=' + Date.now()) : '';
}
async function openLandscapeScr() {
    const wrap = document.getElementById('scr-wrap'), img = document.getElementById('live-scr');
    if (!liveScrOn) toggleLiveScr(); img.style.maxHeight = '100vh';
    try { if (wrap.requestFullscreen) await wrap.requestFullscreen(); if (screen.orientation && screen.orientation.lock) await screen.orientation.lock('landscape'); } catch (e) {}
}
document.addEventListener('fullscreenchange', () => { if (!document.fullscreenElement) document.getElementById('live-scr').style.maxHeight = '240px'; });
async function restartApp() { document.getElementById('mode-pill').textContent = '🔄 Starte neu...'; await fetch('/api/restart', { method: 'POST' }); setTimeout(() => location.reload(), 2800); }

let _vT = 0, _vP = null;
function liveVol(v) {
    v = Math.max(0, Math.min(100, parseInt(v, 10) ? parseInt(v, 10) : 0));
    document.getElementById('vol-rng').value = v; document.getElementById('vol-lbl').textContent = v + ' %'; _vP = v;
    if (Date.now() - _vT > 80) { _vT = Date.now(); fetch('/api/vol', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ v }) }); }
    else { clearTimeout(window._vTm); window._vTm = setTimeout(() => liveVol(_vP), 85); }
}
function stepVol(d) { const cur = parseInt(document.getElementById('vol-rng').value, 10); liveVol((isNaN(cur) ? 50 : cur) + d); }
fetch('/api/vol').then(r => r.json()).then(d => { const el = document.getElementById('vol-rng'); if (el) { el.value = d.v; document.getElementById('vol-lbl').textContent = d.v + ' %'; } }).catch(() => {});
