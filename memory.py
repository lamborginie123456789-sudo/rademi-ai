import os, time, sqlite3, subprocess, winreg, itertools

DB = os.path.join(r"C:\Users\maart\Desktop\KI", "rademi.db")
_NO_WIN = 0x08000000

def _conn():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY AUTOINCREMENT, txt TEXT UNIQUE, ts INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, msg TEXT, ts INTEGER)")
    return c

def add_fact(txt):
    t = txt.strip(" .!?")
    if t:
        with _conn() as c: c.execute("INSERT OR IGNORE INTO facts (txt, ts) VALUES (?, ?)", (t, int(time.time())))

def get_facts():
    with _conn() as c: rows = c.execute("SELECT id, txt FROM facts ORDER BY id DESC LIMIT 25").fetchall()
    return list({"id": r, "txt": next(iter(r[1:]))} for r in rows)

def del_fact(fid):
    with _conn() as c: c.execute("DELETE FROM facts WHERE id = ?", (int(fid),))

def save_msg(role, msg):
    with _conn() as c: c.execute("INSERT INTO chat (role, msg, ts) VALUES (?, ?, ?)", (role, msg, int(time.time())))

def load_history(limit=8):
    with _conn() as c: rows = c.execute("SELECT role, msg FROM chat ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return list((r, next(iter(r[1:]))) for r in reversed(rows))

def get_autostart():
    items = list()
    for root, sub, scope in ((winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Benutzer"), (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "System")):
        try:
            with winreg.OpenKey(root, sub) as k:
                i = 0
                while True:
                    try:
                        n, v, _ = winreg.EnumValue(k, i); items.append({"name": n, "cmd": str(v), "scope": scope}); i += 1
                    except OSError: break
        except Exception: pass
    return items

def del_autostart(name, scope):
    root = winreg.HKEY_CURRENT_USER if scope == "Benutzer" else winreg.HKEY_LOCAL_MACHINE
    try:
        with winreg.OpenKey(root, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
        return True
    except Exception: return False

def rademi_autostart_status():
    r = subprocess.run(list(("schtasks", "/Query", "/TN", "RademiAI_Autostart")), capture_output=True, text=True, creationflags=_NO_WIN)
    return r.returncode == 0

def toggle_rademi_autostart(enable):
    if enable:
        pyw = os.path.join(os.path.dirname(os.sys.executable), "pythonw.exe")
        cmd = f'"{pyw}" "C:\\Users\\maart\\Desktop\\KI\\rademi.py"'
        subprocess.run(list(("schtasks", "/Create", "/TN", "RademiAI_Autostart", "/TR", cmd, "/SC", "ONLOGON", "/RL", "HIGHEST", "/F")), capture_output=True, creationflags=_NO_WIN)
    else:
        subprocess.run(list(("schtasks", "/Delete", "/TN", "RademiAI_Autostart", "/F")), capture_output=True, creationflags=_NO_WIN)
    return rademi_autostart_status()

def search_files(query, limit=15):
    q, hits = query.lower().strip(" .!?\"'"), list()
    if len(q) < 2: return hits
    roots = list(p for p in (os.path.expanduser("~"), "D:\\", "E:\\") if os.path.exists(p))
    skip = {"windows", "program files", "program files (x86)", "appdata", "$recycle.bin", "system volume information", "node_modules", "__pycache__", ".git"}
    for base in roots:
        for root, dirs, files in os.walk(base):
            dirs[:] = list(d for d in dirs if d.lower() not in skip and not d.startswith("."))
            for f in files:
                if q in f.lower():
                    full = os.path.join(root, f)
                    try: sz = f"{round(os.path.getsize(full)/(1024*1024), 1)} MB"
                    except Exception: sz = "?"
                    hits.append({"name": f, "path": full, "dir": root, "size": sz})
                    if len(hits) >= limit: return hits
    return hits
