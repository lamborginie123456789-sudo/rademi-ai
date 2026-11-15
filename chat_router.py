import re, json
import assistant_tools, memory, spotify_ctrl, sys_ctrl, workspace, diagnostics, companion, remote_ctrl

_top, _app = "", ""

def _parse_skip(tl):
    wm = {"ein":1,"eins":1,"zwei":2,"drei":3,"vier":4,"fünf":5,"sechs":6,"sieben":7,"acht":8,"neun":9,"zehn":10}
    m = re.match(r"^(?:(\d+|ein|eins|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn)\s*(?:mal|x)?\s+)?(weiter|skip|skipp|nächstes lied|nächster song|überspringen|weiter skippen|weiter spulen|zurück|vorheriges lied|vorheriger song|zurück skippen|zurück spulen|lied zurück)(?:\s+(\d+)\s*(?:mal|x)?)?$", tl)
    if not m: return None, 1
    rn = m.group(1) or m.group(3) or "1"
    return ("prev" if any(k in m.group(2) for k in ("zurück","vorherig")) else "next"), (int(rn) if rn.isdigit() else wm.get(rn, 1))

def route_command(ein):
    global _top, _app
    tl = ein.lower().strip(" .!?")
    plg = sys_ctrl.run_plugins(ein)
    if plg: return {"antwort": plg, "done": True}
    if any(w in tl for w in ("bildschirm schwarz","schwarzer bildschirm","blackout","screen off")): return {"antwort": sys_ctrl.start_blackout(), "done": True}
    if any(w in tl for w in ("rademi neustart","rademi neu starten")): return {"antwort": remote_ctrl.restart_rademi(), "done": True}
    if any(w in tl for w in ("bluetooth geräte","bluetooth liste","welche bluetooth")): return {"antwort": remote_ctrl.bluetooth_ctrl("list"), "bt_list": remote_ctrl.get_bt_devices(), "done": True}
    if tl.startswith(("bluetooth verbinden", "bluetooth an", "bluetooth ein", "verbinde bluetooth")):
        dev = re.sub(r"^(?:bluetooth\s+(?:verbinden|an|ein)|verbinde\s+bluetooth)(?:\s+mit)?\s*", "", tl).strip()
        return {"antwort": remote_ctrl.bluetooth_ctrl("on", dev), "bt_list": remote_ctrl.get_bt_devices(), "done": True}
    if tl.startswith(("bluetooth trennen", "bluetooth aus", "trenne bluetooth")):
        dev = re.sub(r"^(?:bluetooth\s+(?:trennen|aus)|trenne\s+bluetooth)(?:\s+von)?\s*", "", tl).strip()
        return {"antwort": remote_ctrl.bluetooth_ctrl("off", dev), "bt_list": remote_ctrl.get_bt_devices(), "done": True}
    mc = re.match(r"^(?:schließe|schliesse|beende|close)\s+(.+)$", ein.strip(), re.I)
    if mc: return {"antwort": remote_ctrl.app_window("close", mc.group(1)), "done": True}
    mmn = re.match(r"^minimiere(?:\s+(.+))?$", ein.strip(), re.I)
    if mmn: return {"antwort": remote_ctrl.app_window("min", mmn.group(1) or ""), "done": True}
    mmx = re.match(r"^(?:maximiere|vollbild)(?:\s+(.+))?$", ein.strip(), re.I)
    if mmx: return {"antwort": remote_ctrl.app_window("max", mmx.group(1) or ""), "done": True}
    if any(w in tl for w in ("hey rademi an","wake word an","sprachaktivierung an")): return {"antwort": companion.toggle_wake_word(True), "done": True}
    if any(w in tl for w in ("hey rademi aus","wake word aus","sprachaktivierung aus")): return {"antwort": companion.toggle_wake_word(False), "done": True}
    if any(w in tl for w in ("desktop app","desktop fenster","companion öffnen")): return {"antwort": companion.open_desktop_app(), "done": True}
    if any(w in tl for w in ("backup erstellen","system backup","sicherung erstellen")): return {"antwort": workspace.make_backup(), "done": True}
    if any(w in tl for w in ("clipboard verlauf","zwischenablage verlauf","kopierte texte")): cl = workspace.get_clips(8); return {"antwort": "📋 Letzte Zwischenablagen:\n" + "\n".join(f"• {x['txt'][:80]}" for x in cl) if cl else "📋 Verlauf leer.", "done": True}
    if any(w in tl for w in ("alle fenster minimieren","desktop anzeigen")): return {"antwort": workspace.manage_windows("min_all"), "done": True}
    if "fenster links" in tl: return {"antwort": workspace.manage_windows("snap_left"), "done": True}
    if "fenster rechts" in tl: return {"antwort": workspace.manage_windows("snap_right"), "done": True}
    mw = re.match(r"^(?:workflow|modus|profil)\s+(gaming|arbeit)$", tl)
    if mw: return {"antwort": workspace.run_workflow(mw.group(1)), "done": True}
    if any(w in tl for w in ("benchmark","pc testen","leistungstest")): return {"antwort": diagnostics.run_benchmark(), "done": True}
    if any(w in tl for w in ("benachrichtigungen","warnungen","notification center")): nt = diagnostics.get_notes(); return {"antwort": "🔔 Benachrichtigungen:\n" + "\n".join(f"• {x['ts']}: {x['msg']}" for x in nt) if nt else "🔔 Keine Warnungen.", "done": True}
    if any(w in tl for w in ("windows fehler","fehlerdiagnose","ereignisprotokoll")): return {"llm_prompt": f"Analysiere diese Windows-Fehler auf Deutsch und nenne Lösungen:\n{diagnostics.get_win_errors()}"}
    if any(w in tl for w in ("bildschirm lesen","screenshot analysieren","was ist auf meinem bildschirm")):
        ocr = diagnostics.read_screen_ocr()
        return {"llm_prompt": f"Erkläre mir auf Deutsch, was auf meinem Bildschirm steht:\n\"\"\"\n{ocr[:2500]}\n\"\"\"\nFrage: {ein}"} if ocr else {"antwort": "🖼️ Kein lesbarer Text erkannt.", "done": True}
    if any(w in tl for w in ("ton aus","stumm","mute","ton an","unmute")): return {"antwort": sys_ctrl.set_volume(mute=True), "done": True}
    mv = re.search(r"lautstärke\s+(?:auf\s+)?(\d+)", tl)
    if mv: return {"antwort": sys_ctrl.set_volume(pct=int(mv.group(1))), "done": True}
    mb = re.search(r"helligkeit\s+(?:auf\s+)?(\d+)", tl)
    if mb: return {"antwort": sys_ctrl.set_brightness(int(mb.group(1))), "done": True}
    mt = re.search(r"(?:timer|wecker)\s+(?:auf\s+)?(\d+)\s*(sek|sekunden|min|minuten|std|stunden)?", tl)
    if mt: val, u = int(mt.group(1)), (mt.group(2) or "min"); return {"antwort": sys_ctrl.start_timer(val*3600 if u.startswith("std") else (val if u.startswith("sek") else val*60)), "done": True}
    if any(w in tl for w in ("pc herunterfahren","computer herunterfahren","shutdown")): return {"antwort": sys_ctrl.power_action("shutdown"), "done": True}
    if any(w in tl for w in ("pc neustarten","pc neu starten","computer neu starten")): return {"antwort": sys_ctrl.power_action("reboot"), "done": True}
    if any(w in tl for w in ("energie sparen","energiesparmodus","standby")): return {"antwort": sys_ctrl.power_action("sleep"), "done": True}
    if "zwischenablage" in tl or "kopierten text" in tl: cb = sys_ctrl.get_clipboard(); return {"llm_prompt": f"Zwischenablage:\n\"\"\"\n{cb[:3000]}\n\"\"\"\nAufgabe: {ein}"} if cb else {"antwort": "📋 Zwischenablage leer.", "done": True}
    if tl in ("pause","stop","musik pause","musik stop"): return {"antwort":spotify_ctrl.control("pause"),"done":True}
    if tl in ("play","fortsetzen","abspielen","musik fortsetzen","musik play"): return {"antwort":spotify_ctrl.control("play"),"done":True}
    sa, sc = _parse_skip(tl)
    if sa: return {"antwort":spotify_ctrl.control(sa, count=sc),"done":True}
    ms = re.match(r"^(?:spiele|spiel|mach an)\s+(.+?)(?:\s+(?:auf|über|mit|in)\s+spotify)?(?:\s+ab)?$", ein.strip(), re.I)
    if ms and ms.group(1).lower() not in ("weiter","pause","stop","play","fortsetzen","zurück"): return {"antwort":spotify_ctrl.control("song", ms.group(1)),"done":True}
    mf = re.match(r"^(?:suche datei|finde datei|suche nach|finde)\s+(.+)$", ein.strip(), re.I)
    if mf: q = mf.group(1).strip(); h = memory.search_files(q); return {"antwort":f"📁 Treffer ({len(h)}):" if h else "❌ Nichts gefunden.","files":h,"done":True}
    mm = re.match(r"^(?:merk dir|merke dir|speichere)(?:\s+dass)?[:\s]+(.+)$", ein.strip(), re.I)
    if mm: memory.add_fact(mm.group(1)); return {"antwort":f"🧠 Gespeichert: **{mm.group(1).strip()}**","done":True}
    if any(w in tl for w in ("was weißt du über mich","mein gedächtnis","gespeicherte fakten")): fk = memory.get_facts(); return {"antwort":"🧠 Fakten:\n"+"\n".join(f"• {x['txt']}" for x in fk) if fk else "🧠 Leer.","done":True}
    if any(b in tl for b in ("live-monitor","mini-hud","telemetrie öffnen")): return {"live":True,"done":True}
    ma = re.match(r"^(?:starte|öffne|start|open)\s+(.+)$", ein.strip(), re.I)
    if ma or (_app and any(w in tl for w in ("starte es","öffne es"))): an = ma.group(1).strip() if ma else _app; _app, _top = an, "app"; return {"antwort":assistant_tools.launch_windows_app(an),"done":True}
    if any(z in tl for z in ("wie spät","uhrzeit","zeit in","zeitunterschied")) or (_top=="time" and (any(k in tl for k in assistant_tools.TZ) or any(w in tl for w in ("vergleich","vs","dort","da")))): _top = "time"; t = assistant_tools.get_time_card(ein); return {"antwort":f"Uhrzeit in {t['local_ort']}:" if t["is_single"] else f"Zeitvergleich {t['local_ort']} vs. {t['target_ort']}:","worldtime":t,"done":True}
    if any(w in tl for w in ("wetter","wie warm","temperatur draußen","regnet es")):
        _top = "weather"; m = re.search(r"in\s+([a-zA-ZäöüÄÖÜß\-\s/]+)", ein, re.I); res = assistant_tools.get_weather_card(m.group(1).strip(" ?.!").replace("/", " ") if m else "Herzberg")
        return {"antwort":f"Wetter für {res['data']['ort']}:" if res["type"]=="weather" else f"Ort wählen für „{res['query']}“:","weather":res.get("data"),"city_picker":res if res["type"]=="picker" else None,"done":True}
    if any(s in tl for s in ("specs","mein pc","meine hardware","systemdaten")): _top = "specs"; s = assistant_tools.get_specs_card(); return {"antwort":f"Specs von {s['pc']}:","specs":s,"done":True}
    _top = ""; return None
