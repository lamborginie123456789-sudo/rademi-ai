import time, ctypes, urllib.parse, subprocess

_u32 = ctypes.windll.user32
_NO_WIN = 0x08000000

def _vk(k):
    _u32.keybd_event(k, 0, 0, 0); time.sleep(0.03); _u32.keybd_event(k, 0, 2, 0)

def _min_spotify():
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        _u32.GetWindowTextW(hwnd, buf, 256)
        if "spotify" in (buf.value or "").lower() and _u32.IsWindowVisible(hwnd):
            _u32.ShowWindow(hwnd, 6)
        return True
    _u32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)

def control(action, query="", count=1):
    n = max(1, min(15, int(count)))
    if action in ("pause", "play"):
        _vk(0xB3)
        return "⏯️ Spotify Pause/Play umgeschaltet."
    if action == "next":
        for _ in range(n): _vk(0xB0); time.sleep(0.08)
        return f"⏭️ **{n}x** vorgespult." if n > 1 else "⏭️ Nächster Song."
    if action == "prev":
        for _ in range(n): _vk(0xB1); time.sleep(0.08)
        return f"⏮️ **{n}x** zurückgesprungen." if n > 1 else "⏮️ Vorheriger Song."
    if action == "song" and query:
        q = urllib.parse.quote(query.strip())
        subprocess.Popen(list(("cmd", "/c", f"start spotify:search:{q}")), creationflags=_NO_WIN)
        time.sleep(2.1)
        _vk(0x0D); time.sleep(0.45); _vk(0x20); time.sleep(0.35)
        _min_spotify()
        return f"🎵 Spiele **{query.strip()}** auf Spotify ab (minimiert)."
    return "❓ Unbekannter Spotify-Befehl."
