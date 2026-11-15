function renderTimeCard(t) {
    const b1 = `<div style="background:rgba(15,23,42,.9);padding:12px;border-radius:12px;border:1px solid #1e293b"><div style="display:flex;justify-content:space-between;font-size:.75rem;color:#94a3b8"><span>${t.local_day?'☀️':'🌙'} ${t.local_ort}</span><span>${t.local_tz}</span></div><div style="font-size:1.65rem;font-weight:800;font-family:monospace;color:#f8fafc;margin:4px 0">${t.local_time}</div><div style="font-size:.75rem;color:#64748b;margin-bottom:6px">${t.local_date}</div><div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100-t.local_pct}% 0 0)"></div></div></div>`;
    if (t.is_single) return `<div style="white-space:normal;margin-top:8px;min-width:290px">${b1}</div>`;
    const b2 = `<div style="background:rgba(15,23,42,.9);padding:12px;border-radius:12px;border:1px solid rgba(56,189,248,.45)"><div style="display:flex;justify-content:space-between;font-size:.75rem;color:#38bdf8"><span>${t.target_day?'☀️':'🌙'} ${t.target_ort}</span><span>${t.target_tz}</span></div><div style="font-size:1.65rem;font-weight:800;font-family:monospace;color:#38bdf8;margin:4px 0">${t.target_time}</div><div style="font-size:.75rem;color:#94a3b8;margin-bottom:6px">${t.target_date} · <b>${t.day_diff}</b></div><div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100-t.target_pct}% 0 0)"></div></div></div>`;
    return `<div style="white-space:normal;margin-top:8px;background:rgba(11,16,27,.95);border:1px solid rgba(56,189,248,.35);border-radius:14px;padding:12px;min-width:340px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><strong style="color:#38bdf8;font-size:.82rem">🌍 WELTZEIT-VERGLEICH</strong><span style="font-size:.75rem;padding:2px 10px;border-radius:99px;background:rgba(56,189,248,.16);color:#38bdf8;font-weight:700">${t.diff} (${t.day_diff})</span></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">${b1}${b2}</div></div>`;
}

function renderWeatherCard(w) {
    const tPct = Math.max(4, Math.min(100, ((w.temp + 10) / 45) * 100));
    const daysHtml = (w.days || new Array()).map(d => `<div style="background:rgba(15,23,42,.85);padding:8px 6px;border-radius:10px;text-align:center;flex:1;border:1px solid #1e293b"><div style="color:#94a3b8;font-size:.72rem">${d.date}</div><div style="font-size:1.15rem;margin:2px 0">${d.icon}</div><div style="font-weight:700;font-size:.8rem">${d.min}°/${d.max}°</div><div class="bar-bg" style="height:5px;margin:4px 0"><div class="bar-fill" style="clip-path:inset(0 ${100-Math.max(8,Math.min(100,((d.max+10)/45)*100))}% 0 0)"></div></div><div style="color:#38bdf8;font-size:.7rem">💧${d.rain}%</div></div>`).join('');
    return `<div style="white-space:normal;margin-top:8px;background:rgba(11,16,27,.95);border:1px solid rgba(56,189,248,.4);border-radius:14px;padding:14px;min-width:330px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><div><div style="color:#38bdf8;font-weight:700;font-size:.95rem">${w.icon} ${w.ort}</div><div style="font-size:.78rem;color:#94a3b8">${w.desc} · Gefühlt ${w.feels} °C</div></div><div style="font-size:1.75rem;font-weight:800;font-family:monospace;color:#f8fafc">${w.temp} °C</div></div><div class="bar-bg" style="margin-bottom:10px"><div class="bar-fill" style="clip-path:inset(0 ${100-tPct}% 0 0)"></div></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px;font-size:.74rem;text-align:center"><div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px;border:1px solid #1e293b"><div style="color:#64748b">Feuchte</div><b>${w.hum}%</b></div><div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px;border:1px solid #1e293b"><div style="color:#64748b">Wind</div><b>${w.wind} km/h</b></div><div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px;border:1px solid #1e293b"><div style="color:#64748b">Druck</div><b>${w.press} hPa</b></div><div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px;border:1px solid #1e293b"><div style="color:#64748b">Sonne</div><b>${w.sunrise}–${w.sunset}</b></div></div><div style="display:flex;gap:6px">${daysHtml}</div></div>`;
}

function renderCityPicker(p) {
    const uid = 'cp-' + Math.random().toString(36).slice(2, 8);
    const btns = (p.options && p.options.length) ? p.options.map(o => `<button onclick="selectCityWeather('${uid}',${o.lat},${o.lon},'${o.name.replace(/'/g,'')}')" style="background:rgba(30,41,59,.9);border:1px solid rgba(56,189,248,.35);color:#e2e8f0;padding:8px 12px;border-radius:9px;text-align:left;cursor:pointer;font-size:.82rem">📍 ${o.name}</button>`).join('') : '<div style="color:#94a3b8;font-size:.8rem">Keine direkten Treffer – gib oben einen Ort ein.</div>';
    return `<div id="${uid}" style="white-space:normal;margin-top:8px;background:rgba(11,16,27,.95);border:1px solid rgba(56,189,248,.4);border-radius:14px;padding:14px;min-width:310px"><div style="color:#38bdf8;font-weight:700;font-size:.85rem;margin-bottom:8px">🔍 ORT AUSWÄHLEN ODER SUCHEN</div><div style="display:flex;gap:6px;margin-bottom:10px"><input id="${uid}-in" value="${p.query||''}" placeholder="Ort eingeben..." style="flex:1;background:#0d0f14;border:1px solid #334155;color:#fff;padding:8px 10px;border-radius:8px;font-size:.85rem"><button onclick="searchCityMenu('${uid}')" style="background:#2563eb;color:#fff;border:none;padding:0 12px;border-radius:8px;font-weight:600;cursor:pointer">Suchen</button></div><div id="${uid}-list" style="display:flex;flex-direction:column;gap:6px">${btns}</div></div>`;
}

async function searchCityMenu(uid) {
    const q = document.getElementById(uid + '-in').value.trim(); if (!q) return;
    const el = document.getElementById(uid + '-list'); el.innerHTML = '<div style="color:#94a3b8;font-size:.8rem">Suche Orte...</div>';
    const res = await (await fetch('/api/city_search?q=' + encodeURIComponent(q))).json();
    el.innerHTML = (res && res.length) ? res.map(o => `<button onclick="selectCityWeather('${uid}',${o.lat},${o.lon},'${o.name.replace(/'/g,'')}')" style="background:rgba(30,41,59,.9);border:1px solid rgba(56,189,248,.35);color:#e2e8f0;padding:8px 12px;border-radius:9px;text-align:left;cursor:pointer;font-size:.82rem">📍 ${o.name}</button>`).join('') : '<div style="color:#fca5a5;font-size:.8rem">Nichts gefunden.</div>';
}

async function selectCityWeather(uid, lat, lon, name) {
    const box = document.getElementById(uid); if (!box) return;
    box.innerHTML = '<div style="color:#38bdf8;font-size:.85rem">Lade Wetter für ' + name + '...</div>';
    box.outerHTML = renderWeatherCard(await (await fetch(`/api/weather_coords?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`)).json());
}

function renderFilesCard(files) {
    if (!files || !files.length) return '';
    const rows = files.map(f => {
        const ep = encodeURIComponent(f.path), ed = encodeURIComponent(f.dir);
        return `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;background:rgba(15,23,42,.85);padding:8px 10px;border-radius:9px;border:1px solid #1e293b">
            <div style="min-width:0;overflow:hidden"><div style="font-weight:600;font-size:.82rem;color:#f8fafc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">📄 ${f.name} <span style="color:#64748b;font-weight:400">(${f.size})</span></div><div style="font-size:.7rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.dir}</div></div>
            <div style="display:flex;gap:5px;flex-shrink:0"><button onclick="openLocalPath(decodeURIComponent('${ep}'))" style="background:#2563eb;color:#fff;border:none;padding:5px 9px;border-radius:7px;font-size:.75rem;cursor:pointer">Öffnen</button><button onclick="openLocalPath(decodeURIComponent('${ed}'))" style="background:#1e293b;color:#cbd5e1;border:1px solid #334155;padding:5px 9px;border-radius:7px;font-size:.75rem;cursor:pointer">Ordner</button></div>
        </div>`;
    }).join('');
    return `<div style="white-space:normal;margin-top:8px;background:rgba(11,16,27,.95);border:1px solid rgba(56,189,248,.4);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:6px">${rows}</div>`;
}

async function openLocalPath(p) { await fetch('/api/open_path', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: p }) }); }

function renderSpecsCard(s) {
    const drv = (s.drives || new Array()).map(d => `<div style="margin-top:6px"><div style="display:flex;justify-content:space-between;font-size:.78rem"><span>💾 Laufwerk ${d.mount}</span><span>${d.used_gb}/${d.total_gb} GB (${d.pct}%)</span></div><div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100-Math.max(2,d.pct)}% 0 0)"></div></div></div>`).join('');
    return `<div style="white-space:normal;margin-top:8px;background:rgba(11,16,27,.95);border:1px solid rgba(129,140,248,.4);border-radius:14px;padding:14px;min-width:300px"><div style="color:#818cf8;font-weight:700;margin-bottom:8px">🖥️ SYSTEM-SPECS (${s.pc} · ${s.os})</div><div style="font-size:.82rem;line-height:1.6"><div><b>CPU:</b> ${s.cpu} (${s.cores}) · <span style="color:#38bdf8">${s.cpu_temp} °C</span></div><div><b>GPU:</b> ${s.gpu} (${s.vram}) · <span style="color:#38bdf8">${s.gpu_temp} °C</span></div></div><div style="margin-top:8px"><div style="display:flex;justify-content:space-between;font-size:.78rem"><span>🧠 RAM (${s.ram_total})</span><span>${s.ram_pct}%</span></div><div class="bar-bg"><div class="bar-fill" style="clip-path:inset(0 ${100-Math.max(2,s.ram_pct)}% 0 0)"></div></div></div>${drv}</div>`;
}
