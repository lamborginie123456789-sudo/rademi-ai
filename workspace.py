import os, time, json, ctypes, zipfile, sqlite3, threading, subprocess
import assistant_tools, sys_ctrl

DB = r"C:\Users\maart\Desktop\KI\rademi.db"
_u32 = ctypes.windll.user32
_NO_WIN = 0x08000000

def _conn():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS clips (id INTEGER PRIMARY KEY AUTOINCREMENT, txt TEXT UNIQUE, ts INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS flows (name TEXT PRIMARY KEY, steps TEXT)")
    return c

def start_clip_watcher():
    def _loop():
        last = ""
        while True:
            try:
                cur = sys_ctrl.get_clipboard()
                if cur and cur != last and len(cur) < 5000:
                    last = cur
                    with _conn() as c: c.execute("INSERT OR REPLACE INTO clips (txt, ts) VALUES (?, ?)", (cur, int(time.time())))
            except Exception: pass
            time.sleep(2.5)
    threading.Thread(target=_loop, daemon=True).start()

def get_clips(limit=15):
    with _conn() as c: rows = c.execute("SELECT id, txt FROM clips ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return list({"id": r[0], "txt": r[1]} for r in rows)

def make_backup():
    bdir = r"C:\Users\maart\Desktop\KI\backups"
    os.makedirs(bdir, exist_ok=True)
    zf = os.path.join(bdir, f"rademi_backup_{time.strftime('%Y%m%d_%H%M%S')}.zip")
    with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in os.listdir(r"C:\Users\maart\Desktop\KI"):
            if fn.endswith((".py", ".html", ".css", ".js", ".db")): z.write(os.path.join(r"C:\Users\maart\Desktop\KI", fn), fn)
        pdir = r"C:\Users\maart\Desktop\KI\plugins"
        if os.path.exists(pdir):
            for pfn in os.listdir(pdir): z.write(os.path.join(pdir, pfn), os.path.join("plugins", pfn))
    return f"💾 System-Backup erstellt: **{os.path.basename(zf)}** (im Ordner `backups\\`)"

def manage_windows(act):
    if act == "min_all":
        _u32.keybd_event(0x5B, 0, 0, 0); _u32.keybd_event(0x4D, 0, 0, 0); _u32.keybd_event(0x4D, 0, 2, 0); _u32.keybd_event(0x5B, 0, 2, 0)
        return "🪟 Alle Fenster minimiert."
    if act in ("snap_left", "snap_right"):
        vk = 0x25 if act == "snap_left" else 0x27
        _u32.keybd_event(0x5B, 0, 0, 0); _u32.keybd_event(vk, 0, 0, 0); _u32.keybd_event(vk, 0, 2, 0); _u32.keybd_event(0x5B, 0, 2, 0)
        return "🪟 Aktives Fenster angedockt."
    return ""

def run_workflow(name):
    nl = name.lower().strip()
    if "gaming" in nl:
        subprocess.run(list(("taskkill", "/f", "/im", "chrome.exe")), capture_output=True, creationflags=_NO_WIN)
        assistant_tools.launch_windows_app("steam")
        return "🎮 **Gaming-Workflow gestartet:** Browser geschlossen, Steam gestartet und Gaming-Profil aktiviert!"
    if "arbeit" in nl:
        assistant_tools.launch_windows_app("rechner")
        sys_ctrl.set_brightness(80)
        return "💼 **Arbeits-Workflow gestartet:** Helligkeit auf 80 %, Arbeitsumgebung bereit!"
    with _conn() as c:
        row = c.execute("SELECT steps FROM flows WHERE lower(name) = ?", (nl,)).fetchone()
    if row:
        for app in json.loads(row[0]): assistant_tools.launch_windows_app(app); time.sleep(0.4)
        return f"⚡ Workflow **{name}** ausgeführt."
    return f"❓ Workflow **{name}** nicht gefunden. Verfügbar: *Gaming*, *Arbeit*."
