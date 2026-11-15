import os, ctypes, socket, random, subprocess, urllib.request

_NO_WIN = 0x08000000
PIN = str(random.randint(1000, 9999))

def get_free_port(start=5005):
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start

def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return next(iter(s.getsockname()))
    except Exception:
        return "127.0.0.1"

def open_firewall(port):
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return
        cmd = f'netsh advfirewall firewall delete rule name="RADEMI_AUTO" & netsh advfirewall firewall add rule name="RADEMI_AUTO" dir=in action=allow protocol=TCP localport={port} profile=any'
        subprocess.Popen(list(("cmd", "/c", cmd)), creationflags=_NO_WIN)
    except Exception:
        pass

def download_default_model(app_dir, cb_status):
    url = "https://huggingface.co"
    dest = os.path.join(app_dir, "Qwen2.5-3B-Instruct-Q4_K_M.gguf")
    try:
        cb_status("⏳ Lade Standard-KI (Qwen 2.5 3B, ca. 2 GB) herunter...")
        urllib.request.urlretrieve(url, dest)
        cb_status("✅ KI-Modell heruntergeladen! Lade KI...")
        return True
    except Exception as e:
        cb_status(f"⚠️ Download-Fehler: {e}")
        return False
