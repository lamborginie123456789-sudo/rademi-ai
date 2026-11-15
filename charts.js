window.activeView = 'chat';
let dismissedAlerts = '';
const hud = document.getElementById('hud'), hh = document.getElementById('hud-head');
let drag = false, ox = 0, oy = 0;

if (hh) {
    hh.onmousedown = e => { drag = true; const r = hud.getBoundingClientRect(); ox = e.clientX - r.left; oy = e.clientY - r.top; hud.style.right = 'auto'; };
    document.onmousemove = e => { if (!drag) return; hud.style.left = Math.max(0, Math.min(innerWidth - hud.offsetWidth, e.clientX - ox)) + 'px'; hud.style.top = Math.max(0, Math.min(innerHeight - hud.offsetHeight, e.clientY - oy)) + 'px'; };
    document.onmouseup = () => drag = false;
}
function toggleHud() { if (hud) hud.style.display = hud.style.display === 'block' ? 'none' : 'block'; }
function closeAlert(sig) { dismissedAlerts = sig; const ab = document.getElementById('alert-bar'); if (ab) ab.style.display = 'none'; }
function setTxt(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function setArc(id, pct) { const el = document.getElementById(id); if (el) el.style.strokeDashoffset = 220 - (220 * Math.max(0, Math.min(100, pct)) / 100); }
function setBar(id, pct) { const el = document.getElementById(id); if (el) el.style.clipPath = 'inset(0 ' + (100 - Math.max(2, Math.min(100, pct))) + '% 0 0)'; }

function drawChart(canvasId, data, color, maxVal = 100) {
    const c = document.getElementById(canvasId);
    if (!c || !data || data.length < 2) return;
    const ctx = c.getContext('2d'), w = c.width = c.clientWidth || 400, h = c.height = 150;
    ctx.clearRect(0, 0, w, h); ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    for (let i = 1; i < 4; i++) { ctx.beginPath(); ctx.moveTo(0, (h / 4) * i); ctx.lineTo(w, (h / 4) * i); ctx.stroke(); }
    ctx.beginPath();
    data.forEach((v, idx) => { const x = (idx / (data.length - 1)) * w, y = h - (Math.min(maxVal, Math.max(0, v)) / maxVal) * (h - 16) - 8; idx === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); });
    ctx.strokeStyle = color; ctx.lineWidth = 2.2; ctx.stroke(); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fillStyle = color.replace('1)', '0.15)'); ctx.fill();
}

async function updateTelemetry() {
    try {
        const d = await (await fetch('/telemetry')).json();
        const ab = document.getElementById('alert-bar');
        if (ab && d.alerts && d.alerts.length) {
            const sig = d.alerts.map(a => a.level).join(',');
            if (sig !== dismissedAlerts) { ab.style.display = 'flex'; ab.style.justifyContent = 'space-between'; ab.innerHTML = `<span>⚠️ ${d.alerts.map(a => a.msg).join(' | ')}</span><button onclick="closeAlert('${sig}')" style="background:none;border:none;color:#fca5a5;font-size:1rem;cursor:pointer;padding:0 6px">✕</button>`; }
        } else if (ab) { dismissedAlerts = ''; ab.style.display = 'none'; }

        setTxt('h-mhz', d.cpu_mhz); setTxt('h-cval', d.cpu_load.toFixed(1) + ' %'); setBar('h-cbar', d.cpu_load);
        setTxt('h-ctemp', d.cpu_temp); setBar('h-ctbar', d.cpu_temp_pct);
        setTxt('h-gtemp', d.gpu_temp); setTxt('h-gwatt', d.gpu_watt); setTxt('h-gval', d.gpu_load.toFixed(1) + ' %'); setBar('h-gbar', d.gpu_load);
        setTxt('h-vgb', d.vram_text); setTxt('h-vval', d.vram_pct.toFixed(1) + ' %'); setBar('h-vbar', d.vram_pct);
        setTxt('h-rgb', d.ram_text); setTxt('h-rval', d.ram_pct.toFixed(1) + ' %'); setBar('h-rbar', d.ram_pct);
        setTxt('h-dgb', d.disk_text); setTxt('h-dval', d.disk_pct.toFixed(1) + ' %'); setBar('h-dbar', d.disk_pct);
        setTxt('h-dn', d.net_down.toFixed(2)); setTxt('h-up', d.net_up.toFixed(2)); setTxt('h-ping', d.ping_ms >= 0 ? d.ping_ms : '--');

        if (window.activeView === 'dash') {
            setTxt('d-cwatt', d.cpu_watt + ' W'); setTxt('v-ctemp', d.cpu_temp + ' °C'); setArc('g-ctemp', d.cpu_temp_pct); setTxt('s-cpu', `Last: ${d.cpu_load.toFixed(1)}% · ${d.cpu_mhz} MHz`);
            setTxt('d-gwatt', d.gpu_watt + ' W'); setTxt('v-gtemp', d.gpu_temp + ' °C'); setArc('g-gtemp', Number(d.gpu_temp) || 0); setTxt('s-gpu', `Last: ${d.gpu_load.toFixed(0)}% · VRAM: ${d.vram_text}`);
            setTxt('d-ramgb', d.ram_text); setTxt('v-ram', d.ram_pct.toFixed(0) + ' %'); setArc('g-ram', d.ram_pct); setTxt('s-ram', `Verfügbar: ${d.ram_avail_gb} GB`);
            setTxt('d-diskgb', d.disk_text); setTxt('v-disk', d.disk_pct.toFixed(0) + ' %'); setArc('g-disk', d.disk_pct); setTxt('s-disk', `R: ${d.disk_read_mb} MB/s · W: ${d.disk_write_mb} MB/s`);
            setTxt('c-live-pct', d.cpu_load.toFixed(1) + ' %'); setTxt('g-live-pct', d.gpu_load.toFixed(1) + ' %');
            drawChart('chart-cpu', d.history.cpu, 'rgba(56, 189, 248, 1)'); drawChart('chart-gpu', d.history.gpu, 'rgba(16, 185, 129, 1)');

            const fl = document.getElementById('fan-list');
            if (fl) {
                const fanCards = (d.fans && d.fans.length) ? d.fans.map(f => `<div class="core-box" style="border-color:rgba(56,189,248,.35)"><div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="color:#38bdf8;font-weight:600">🌀 ${f.name}</span><span style="font-family:monospace;font-weight:700">${f.rpm} RPM</span></div><div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100 - Math.max(4, f.pct || 20)}% 0 0)"></div></div></div>`).join('') : '';
                const sensorCards = (d.extra_sensors || new Array()).map(s => `<div class="core-box"><div style="display:flex;justify-content:space-between"><span style="color:#cbd5e1;font-weight:600">${s.name}</span><span style="font-family:monospace;font-weight:700;color:#38bdf8">${s.val}</span></div><div style="font-size:.72rem;color:#64748b;margin-top:2px">${s.sub}</div></div>`).join('');
                fl.style.gridTemplateColumns = 'repeat(auto-fit, minmax(240px, 1fr))';
                fl.innerHTML = (fanCards + sensorCards) || '<div class="core-box">Alle Hauptsensoren oben aktiv</div>';
            }
        }
        if (window.activeView === 'cpu') {
            setTxt('cpu-detail-head', `${d.cpu_cores} Threads · ${d.cpu_mhz} MHz · ${d.cpu_watt} W`);
            const cg = document.getElementById('core-grid');
            if (cg) cg.innerHTML = (d.cpu_per_core || new Array()).map((v, i) => `<div class="core-box"><strong>Core #${i}</strong>: ${v.toFixed(1)} %<div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100 - Math.max(2, v)}% 0 0)"></div></div></div>`).join('');
            const ctg = document.getElementById('core-temp-grid');
            if (ctg) ctg.innerHTML = (d.cpu_core_temps || new Array()).map(c => `<div class="core-box"><strong>${c.name}</strong><br>${c.temp} °C</div>`).join('') || '<div class="core-box">Keine Einzelkern-Temps</div>';
        }
        if (window.activeView === 'gpu') {
            setTxt('gpu-model-name', d.gpu_name); setTxt('gpu-clk-badge', d.gpu_clock + ' MHz');
            const gd = document.getElementById('gpu-details');
            if (gd) gd.innerHTML = `<div class="core-box"><strong>Core Last</strong><br>${d.gpu_load} %</div><div class="core-box"><strong>Memory Ctrl</strong><br>${d.gpu_mem_ctrl} %</div><div class="core-box"><strong>Temperatur</strong><br>${d.gpu_temp} °C</div><div class="core-box"><strong>Verbrauch / Lüfter</strong><br>${d.gpu_watt} W · ${d.gpu_fan} %</div>`;
        }
        if (window.activeView === 'ram') { setTxt('ram-detail-txt', `${d.ram_text} (Frei: ${d.ram_avail_gb} GB)`); drawChart('chart-ram', d.history.ram, 'rgba(245, 158, 11, 1)'); }
        if (window.activeView === 'drives') {
            setTxt('io-txt', `Lesen: ${d.disk_read_mb} MB/s · Schreiben: ${d.disk_write_mb} MB/s`);
            const dl = document.getElementById('drives-list');
            if (dl) dl.innerHTML = (d.drives || new Array()).map(dr => `<div class="core-box"><strong>Laufwerk ${dr.mount}</strong> (${dr.used_gb} / ${dr.total_gb} GB · ${dr.pct}%)<div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100 - Math.max(2, dr.pct)}% 0 0)"></div></div></div>`).join('');
        }
        if (window.activeView === 'net') {
            setTxt('net-status', `${d.net_online ? 'Online' : 'Offline'} · Ping: ${d.ping_ms} ms · ⬇ ${d.net_down} MB/s · ⬆ ${d.net_up} MB/s`);
            const arr = Array.isArray(d.history.net_down) ? d.history.net_down : new Array();
            drawChart('chart-net', arr, 'rgba(129, 140, 248, 1)', Math.max(10, ...arr));
        }
    } catch (e) {}
    setTimeout(updateTelemetry, 500);
}
updateTelemetry();
