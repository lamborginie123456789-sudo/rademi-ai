import os, sys, glob, time, ctypes, threading, subprocess, importlib.util

_u32 = ctypes.windll.user32
_NO_WIN = 0x08000000
_blk_proc = None

def _vk(k):
    _u32.keybd_event(k, 0, 0, 0); time.sleep(0.03); _u32.keybd_event(k, 0, 2, 0)

def set_volume(pct=None, mute=False):
    if mute:
        _vk(0xAD)
        return "🔇 Ton umgeschaltet (Stumm/An)."
    p = max(0, min(100, int(pct)))
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        dev = AudioUtilities.GetSpeakers()
        vol = dev.EndpointVolume
        vol.SetMasterVolumeLevelScalar(p / 100.0, None)
        return f"🔊 Lautstärke direkt auf **{p} %** gesetzt."
    except Exception as e:
        return f"⚠️ Lautstärke-Fehler: {e}"

def set_brightness(pct):
    p = max(5, min(100, int(pct)))
    ps = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{p})"
    subprocess.run(list(("powershell", "-NoProfile", "-Command", ps)), capture_output=True, creationflags=_NO_WIN)
    return f"☀️ Bildschirmhelligkeit auf **{p} %** gesetzt."

def start_blackout():
    global _blk_proc
    if _blk_proc and _blk_proc.poll() is None:
        _blk_proc.terminate()
        _blk_proc = None
        return "🖥️ Schwarzer Bildschirm beendet."
    _blk_proc = subprocess.Popen(list((sys.executable, r"C:\Users\maart\Desktop\KI\blackout.py")), creationflags=_NO_WIN)
    return "⬛ Schwarzer Bildschirm aktiv (erneut tippen, Taste drücken oder Maus bewegen zum Beenden)."

def power_action(act):
    if act == "shutdown": subprocess.Popen(list(("shutdown", "/s", "/t", "15")), creationflags=_NO_WIN); return "🛑 PC fährt in 15 Sek. herunter."
    if act == "reboot": subprocess.Popen(list(("shutdown", "/r", "/t", "15")), creationflags=_NO_WIN); return "🔄 PC startet in 15 Sek. neu."
    if act == "sleep": subprocess.Popen(list(("rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0")), creationflags=_NO_WIN); return "💤 Energiesparmodus wird aktiviert."
    return ""

def start_timer(sek, label="Timer"):
    def _done(): time.sleep(sek); _u32.MessageBoxW(0, f"⏰ {label} ist abgelaufen!", "RADEMI AI Timer", 0x40 | 0x40000)
    threading.Thread(target=_done, daemon=True).start()
    m, s = divmod(sek, 60)
    return f"⏱️ **{label}** gestartet (**{m} Min. {s} Sek.**)!"

def get_clipboard():
    r = subprocess.run(list(("powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw")), capture_output=True, text=True, creationflags=_NO_WIN)
    return (r.stdout or "").strip()

def run_plugins(ein):
    for f in glob.glob(r"C:\Users\maart\Desktop\KI\plugins\*.py"):
        try:
            spec = importlib.util.spec_from_file_location("plg", f)
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            if hasattr(mod, "handle"):
                res = mod.handle(ein)
                if res: return str(res)
        except Exception: pass
    return None
