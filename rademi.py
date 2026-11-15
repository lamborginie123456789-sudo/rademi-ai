import sys, os, io, re, gc, time, json, urllib.request, traceback, platform, threading, webbrowser, itertools, subprocess, psutil
from flask import Flask, request, jsonify, send_file, Response, stream_with_context

APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)
os.chdir(APP_DIR)
if sys.stdout is None: sys.stdout = open(os.devnull, "w")
if sys.stderr is None: sys.stderr = open(os.path.join(APP_DIR, "fehler.log"), "w")
import hardware, tools, assistant_tools, memory, chat_router, workspace, diagnostics, companion, remote_ctrl, hud_overlay, net_setup

PORT = net_setup.get_free_port(5005)
LAN_URL = f"http://{net_setup.get_lan_ip()}:{PORT}"
MASTER_REPORT_URL = ""
threading.Thread(target=lambda: net_setup.open_firewall(PORT), daemon=True).start()

kerne = max(1, (os.cpu_count() or 4) // 2)
_std_llm, _pwr_llm, fehler, modus, profil, wechsel = None, None, None, "standard", "arbeit", False
_pc_queue = list()
_err_logs = list()
_seen_errs = set()
_lock = threading.Lock()
S, E = "<|" + "im_start|>", "<|" + "im_end|>"

def _forward_remote(src, detail, host_name):
    if not MASTER_REPORT_URL: return
    try:
        data = json.dumps({"src": f"{host_name} · {src}", "msg": str(detail)[:700], "remote": True}).encode("utf-8")
        req = urllib.request.Request(MASTER_REPORT_URL.rstrip("/") + "/api/report_error", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=4)
    except Exception:
        pass

def log_code_error(src, detail, host_name="", is_remote=False):
    hn = host_name or platform.node()
    sig = f"{hn}:{src}:{str(detail)[:80]}"
    if sig in _seen_errs: return
    _seen_errs.add(sig)
    _err_logs.insert(0, {"id": int(time.time() * 1000), "time": time.strftime("%H:%M:%S"), "host": hn, "remote": is_remote, "src": str(src), "msg": str(detail)[:800]})
    del _err_logs[50:]
    if not is_remote and MASTER_REPORT_URL:
        threading.Thread(target=_forward_remote, args=(src, detail, hn), daemon=True).start()

def _sys_excepthook(exc_type, exc_val, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))[-500:]
    log_code_error("Python-Crash", tb)
    sys.__excepthook__(exc_type, exc_val, exc_tb)

sys.excepthook = _sys_excepthook

def _find_mod(m):
    lst = (("Qwen_Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf",22),("Qwen2.5-14B-Instruct-Q4_K_M.gguf",36),("Qwen2.5-7B-Instruct-Q4_K_M.gguf",-1)) if m=="leistung" else (("Qwen2.5-3B-Instruct-Q4_K_M.gguf",-1),("Qwen2.5-7B-Instruct-Q4_K_M.gguf",-1),("modell.gguf",-1))
    for d, l in lst:
        p = os.path.join(APP_DIR, d)
        if os.path.exists(p): return p, l
    return None, -1

def lade_ki(m="standard"):
    global _std_llm, _pwr_llm, fehler, modus, wechsel
    with _lock:
        wechsel, fehler = True, None
        try:
            from llama_cpp import Llama
            if m == "gaming":
                if _pwr_llm is not None: _pwr_llm.close(); _pwr_llm = None; gc.collect()
                modus = "gaming"
            elif m == "leistung":
                if _pwr_llm is None:
                    d, l = _find_mod("leistung")
                    if not d: fehler = "NO_MODEL"; wechsel = False; return
                    _pwr_llm = Llama(model_path=d, n_gpu_layers=l, n_threads=kerne, n_batch=256, n_ctx=2048, use_mmap=True, flash_attn=True, verbose=False)
                modus = "leistung"
            else:
                if _pwr_llm is not None: _pwr_llm.close(); _pwr_llm = None; gc.collect()
                if _std_llm is None:
                    d, l = _find_mod("standard")
                    if not d: fehler = "NO_MODEL"; wechsel = False; return
                    _std_llm = Llama(model_path=d, n_gpu_layers=l, n_threads=kerne, n_batch=256, n_ctx=2048, use_mmap=True, flash_attn=True, verbose=False)
                modus = "standard"
        except Exception as e:
            fehler = f"Ladefehler: {e}"
            log_code_error("KI-Loader", e)
        wechsel = False

def prompt_bau(e):
    kurz = e[:1800]; memory.save_msg("user", kurz[:300]); fk = memory.get_facts()
    ft = ("\nFakten:\n" + "\n".join(f"- {x['txt']}" for x in fk)) if fk else ""
    sm = f"Du bist Rademi, ein herzlicher, lockerer Windows-11-Assistent. Antworte natürlich auf Deutsch, nutze gerne Markdown (Fettschrift, Listen, Code-Blöcke) und duze den Nutzer.{ft}"
    hist = "".join(f"{S}{r}\n{m[:300]}{E}\n" for r, m in memory.load_history(2)[:-1])
    return f"{S}system\n{sm}{E}\n{hist}{S}user\n{kurz}{E}\n{S}assistant\n"
app = Flask(__name__); app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.errorhandler(Exception)
def handle_flask_err(e):
    tb = traceback.format_exc()[-450:]
    log_code_error(f"Route {request.path}", tb)
    return jsonify({"antwort": f"⚠️ Server-Fehler gemeldet: {e}"}), 500

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Pin"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp

@app.before_request
def guard():
    if request.method == "OPTIONS": return "", 204
    if request.path == "/api/report_error": return
    if request.remote_addr in ("127.0.0.1", "::1"): return
    if request.path.startswith("/api/") or request.path == "/chat_stream":
        if request.headers.get("X-Pin") != net_setup.PIN and request.args.get("pin") != net_setup.PIN:
            return jsonify({"antwort": "🔒 Bitte zuerst die 4-stellige PC-PIN eingeben!"}), 401

@app.route("/")
def r_idx(): return send_file(os.path.join(RES_DIR, "index.html"))
@app.route("/style.css")
def r_css(): return send_file(os.path.join(RES_DIR, "style.css"))
@app.route("/charts.js")
def r_chr(): return send_file(os.path.join(RES_DIR, "charts.js"))
@app.route("/cards.js")
def r_crd(): return send_file(os.path.join(RES_DIR, "cards.js"))
@app.route("/app.js")
def r_app(): return send_file(os.path.join(RES_DIR, "app.js"))
@app.route("/manifest.json")
def r_man(): return jsonify({"name":"RADEMI AI","short_name":"RADEMI","start_url":"/","display":"standalone","background_color":"#050811","theme_color":"#38bdf8","icons":[{"src":"/icon.png","sizes":"256x256","type":"image/png"}]})
@app.route("/icon.png")
def r_icn():
    from PIL import Image
    buf = io.BytesIO(); Image.open(os.path.join(RES_DIR, "rademi.ico")).save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png")
@app.route("/api/qr.png")
def r_qr():
    import qrcode
    buf = io.BytesIO(); qrcode.make(LAN_URL).save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png")
@app.route("/api/connect_info")
def r_inf(): return jsonify({"url": LAN_URL, "pin": net_setup.PIN, "local": request.remote_addr in ("127.0.0.1", "::1"), "no_model": fehler == "NO_MODEL"})
@app.route("/api/report_error", methods=("POST",))
def r_err():
    d = request.json or {}
    is_rem = bool(d.get("remote")) or (request.remote_addr not in ("127.0.0.1", "::1"))
    log_code_error(d.get("src", "Browser-UI"), d.get("msg", "Unbekannter Fehler"), d.get("host", request.remote_addr or ""), is_rem)
    return jsonify({"ok": True})
@app.route("/api/errors", methods=("GET", "DELETE"))
def r_errs():
    if request.method == "DELETE":
        _err_logs.clear(); _seen_errs.clear()
        return jsonify({"ok": True})
    return jsonify(_err_logs)
@app.route("/api/pc_chat", methods=("GET", "POST"))
def r_pcc():
    if request.method == "POST":
        txt = (request.json or {}).get("prompt", "").strip()
        if txt: _pc_queue.append(txt)
        return jsonify({"antwort": f"📨 Auf dem PC-Bildschirm an Rademi gesendet: **{txt}**"})
    msg = _pc_queue.pop(0) if _pc_queue else ""
    return jsonify({"prompt": msg})
@app.route("/api/clipboard_sync", methods=("GET", "POST"))
def r_clps():
    if request.method == "POST":
        txt = (request.json or {}).get("text", "")
        return jsonify({"antwort": remote_ctrl.set_pc_clipboard(txt)})
    return jsonify({"text": remote_ctrl.get_pc_clipboard()})
@app.route("/api/download_model", methods=("POST",))
def r_dlm():
    def _dl():
        global fehler
        if net_setup.download_default_model(APP_DIR, lambda msg: globals().update(fehler=msg)): lade_ki("standard")
    threading.Thread(target=_dl, daemon=True).start(); return jsonify({"ok": True})
@app.route("/api/vol", methods=("GET","POST"))
def r_vol():
    import comtypes; from pycaw.pycaw import AudioUtilities; comtypes.CoInitialize(); v = AudioUtilities.GetSpeakers().EndpointVolume
    if request.method == "POST": v.SetMasterVolumeLevelScalar(max(0,min(100,int(request.json.get("v",50))))/100.0, None)
    return jsonify({"v": round(v.GetMasterVolumeLevelScalar()*100)})
@app.route("/api/mouse", methods=("POST",))
def r_mse(): d = request.json or {}; return jsonify({"msg": remote_ctrl.mouse_ctrl(d.get("dx", 0), d.get("dy", 0), d.get("click", ""))})
@app.route("/api/key", methods=("POST",))
def r_key(): d = request.json or {}; return jsonify({"antwort": remote_ctrl.key_ctrl(d.get("key", ""), d.get("text", ""))})
@app.route("/telemetry")
def r_tel(): return jsonify(hardware.get_telemetrie())
@app.route("/api/restart", methods=("POST",))
def r_rst(): return jsonify({"msg": remote_ctrl.restart_rademi()})
@app.route("/api/stream.mjpg")
def r_mjp(): return Response(stream_with_context(remote_ctrl.mjpeg_stream()), mimetype="multipart/x-mixed-replace; boundary=frame")
@app.route("/api/screen")
def r_scr(): res = remote_ctrl.get_live_jpeg(); return send_file(res, mimetype="image/jpeg")
@app.route("/api/remote_cmd", methods=("POST",))
def r_rmt():
    cmd = request.json.get("cmd", "")
    if cmd == "lock": return jsonify({"antwort": remote_ctrl.lock_pc()})
    r = chat_router.route_command(cmd); return jsonify(r if r else {"antwort": "✅ Befehl ausgeführt."})
@app.route("/api/hud_overlay", methods=("POST",))
def r_hud(): return jsonify({"active": hud_overlay.toggle_hud()})
@app.route("/api/clips")
def r_clp(): return jsonify(workspace.get_clips(10))
@app.route("/api/notes")
def r_nts(): return jsonify(diagnostics.get_notes())
@app.route("/api/launch", methods=("POST",))
def r_lnc(): return jsonify({"msg": assistant_tools.launch_windows_app(request.json.get("app", ""))})
@app.route("/api/autostart", methods=("GET","POST","DELETE"))
def r_aut():
    if request.method == "POST": return jsonify({"rademi": memory.toggle_rademi_autostart(bool(request.json.get("enable")))})
    if request.method == "DELETE": return jsonify({"ok": memory.del_autostart(request.args.get("name",""), request.args.get("scope",""))})
    return jsonify({"items": memory.get_autostart(), "rademi": memory.rademi_autostart_status()})
@app.route("/api/open_path", methods=("POST",))
def r_opn(): p = request.json.get("path", ""); os.startfile(p) if p and os.path.exists(p) else None; return jsonify({"ok": bool(p)})
@app.route("/api/facts", methods=("GET","POST","DELETE"))
def r_fct():
    if request.method == "POST": memory.add_fact(request.json.get("txt", ""))
    elif request.method == "DELETE": memory.del_fact(request.args.get("id", 0))
    return jsonify(memory.get_facts())
@app.route("/api/city_search")
def r_cts(): return jsonify(assistant_tools.search_cities(request.args.get("q", "")))
@app.route("/api/weather_coords")
def r_wth(): return jsonify(assistant_tools.get_weather_by_coords(float(request.args.get("lat", 51.69)), float(request.args.get("lon", 13.23)), request.args.get("name", "Herzberg")))
@app.route("/api/mode", methods=("GET", "POST"))
def r_mod():
    global profil
    if request.method == "POST" and not wechsel:
        profil = request.json.get("profile", profil)
        if request.json.get("mode") != modus: threading.Thread(target=lade_ki, args=(request.json.get("mode", "standard"),), daemon=True).start()
    return jsonify({"mode": modus, "profile": profil, "switching": wechsel})
@app.route("/api/processes")
def r_prc():
    p = list({"pid": x.info["pid"], "name": x.info["name"] or "?", "cpu": round(x.info["cpu_percent"] or 0.0, 1), "ram_mb": round(x.info["memory_info"].rss/(1024**2), 1) if x.info["memory_info"] else 0.0} for x in psutil.process_iter(list(("pid","name","cpu_percent","memory_info"))))
    p.sort(key=lambda x: x["ram_mb"], reverse=True); return jsonify(list(itertools.islice(p, 35)))
@app.route("/api/system")
def r_sys(): return jsonify({"os": f"{platform.system()} {platform.release()}", "pc_name": platform.node(), "arch": platform.machine(), "cpu": platform.processor(), "boot_time": time.strftime("%d.%m.%Y %H:%M", time.localtime(psutil.boot_time()))})

@app.route("/chat_stream", methods=("POST",))
def r_cht():
    ein = request.json.get("prompt", "")
    def gen():
        try:
            cmd_res = chat_router.route_command(ein)
            if cmd_res is not None and "llm_prompt" not in cmd_res: yield json.dumps(cmd_res)+"\n"; return
            if modus == "gaming": yield json.dumps({"antwort":"🎮 Ich bin im Gaming-Modus und halte deinen VRAM frei. Wechsel auf **💼 Arbeit** oder **🧠 KI-Power**, wenn wir quatschen sollen!","done":True})+"\n"; return
            ziel_ein = cmd_res["llm_prompt"] if cmd_res else ein
            with _lock:
                akt_llm = _pwr_llm if modus == "leistung" else _std_llm
                if fehler == "NO_MODEL": yield json.dumps({"antwort":"📥 Kein KI-Modell gefunden! Öffne **📱 Handy-Remote** und klicke auf **KI-Modell herunterladen** (oder lege eine .gguf-Datei in den Rademi-Ordner).","done":True})+"\n"; return
                if fehler or akt_llm is None: yield json.dumps({"antwort":fehler or "Modell lädt noch kurz...","done":True})+"\n"; return
                pr, voll, thk = prompt_bau(ziel_ein), "", False
                for ch in akt_llm(pr, max_tokens=(700 if modus=="leistung" else 400), temperature=0.35, top_p=0.9, repeat_penalty=1.1, stop=list((E,)), stream=True):
                    tok = next(iter(ch["choices"]))["text"]; voll += tok
                    if "<think>" in tok: thk = True
                    if "</think>" in tok: thk = False; continue
                    if not thk and "<think>" not in tok: yield json.dumps({"token":tok})+"\n"
                ant = re.sub(r"<think>.*?</think>", "", voll, flags=re.S).strip() or "Alles klar!"; memory.save_msg("assistant", ant); yield json.dumps({"antwort":ant,"done":True})+"\n"
        except Exception as ex:
            log_code_error("Chat-Stream", ex)
            yield json.dumps({"antwort":f"⚠️ Fehler: {ex}","done":True})+"\n"
    return Response(stream_with_context(gen()), mimetype="application/x-ndjson")

@app.route("/audio", methods=("POST",))
def r_aud(): return jsonify({"text": tools.audio_aufnehmen(5)})

def _bg_init():
    hardware.starte_telemetrie(); workspace.start_clip_watcher(); diagnostics.start_temp_logger(); companion.start_hotkey_listener(); lade_ki("standard")

if __name__ == "__main__":
    threading.Timer(0.05, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    threading.Timer(0.4, _bg_init).start()
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)
