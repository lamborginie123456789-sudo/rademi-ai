import os, time, ctypes, threading, subprocess, webbrowser
import tools

_u32 = ctypes.windll.user32
_NO_WIN = 0x08000000
_wake_active = False

def open_desktop_app():
    found = list()
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        _u32.GetWindowTextW(hwnd, buf, 256)
        if "rademi" in (buf.value or "").lower() and _u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    _u32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
    if found:
        hwnd = found
        _u32.ShowWindow(hwnd, 9)
        _u32.SetForegroundWindow(hwnd)
        return "🖥️ Rademi-Fenster nach vorne geholt!"
    url = "http://127.0.0.1:5005"
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if os.path.exists(p):
            subprocess.Popen(list((p, f"--app={url}", "--new-window", "--window-size=1180,760")), creationflags=_NO_WIN)
            return "🖥️ Rademi Desktop-Fenster geöffnet!"
    webbrowser.open(url)
    return "🌐 Rademi im Browser geöffnet."

def start_hotkey_listener():
    def _loop():
        while True:
            try:
                r_down = (_u32.GetAsyncKeyState(0x52) & 0x8000) != 0
                o_down = (_u32.GetAsyncKeyState(0x4F) & 0x8000) != 0
                if r_down and o_down:
                    open_desktop_app()
                    time.sleep(1.2)
            except Exception: pass
            time.sleep(0.03)
    threading.Thread(target=_loop, daemon=True).start()

def toggle_wake_word(enable):
    global _wake_active
    _wake_active = bool(enable)
    if _wake_active:
        def _listen():
            while _wake_active:
                try:
                    txt = (tools.audio_aufnehmen(3) or "").lower()
                    if any(w in txt for w in ("hey rademi", "hallo rademi", "rademi")):
                        open_desktop_app()
                except Exception: pass
                time.sleep(0.4)
        threading.Thread(target=_listen, daemon=True).start()
        return "🎙️ Aktivierungswort **„Hey Rademi“** ist jetzt **AN**."
    return "🔇 Aktivierungswort **„Hey Rademi“** wurde deaktiviert."
