import os, io, time, ctypes, threading, subprocess, psutil

_u32 = ctypes.windll.user32
_NO_WIN = 0x08000000

def _ws_mouse_loop():
    import asyncio, websockets
    async def handler(ws):
        async for msg in ws:
            try:
                sx, sy = msg.split(",", 1)
                dx, dy = int(sx), int(sy)
                if dx or dy: _u32.mouse_event(0x0001, dx, dy, 0, 0)
            except Exception: pass
    async def main():
        async with websockets.serve(handler, "0.0.0.0", 5009):
            await asyncio.Future()
    try: asyncio.run(main())
    except Exception: pass

threading.Thread(target=_ws_mouse_loop, daemon=True).start()

def restart_rademi():
    cmd = '/c timeout /t 1 /nobreak >nul & taskkill /f /im pythonw.exe & rmdir /s /q "C:\\Users\\maart\\Desktop\\KI\\__pycache__" 2>nul & start "" pythonw "C:\\Users\\maart\\Desktop\\KI\\rademi.py"'
    subprocess.Popen(list(("cmd", cmd)), creationflags=_NO_WIN)
    return "🔄 Rademi wird neu gestartet..."

def lock_pc():
    _u32.LockWorkStation()
    return "🔒 PC gesperrt."

def mouse_ctrl(dx=0, dy=0, click=""):
    if dx or dy: _u32.mouse_event(0x0001, int(dx), int(dy), 0, 0)
    if click == "left": _u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.015); _u32.mouse_event(0x0004, 0, 0, 0, 0)
    elif click == "right": _u32.mouse_event(0x0008, 0, 0, 0, 0); time.sleep(0.015); _u32.mouse_event(0x0010, 0, 0, 0, 0)
    return "OK"

def _combo(*keys):
    for k in keys: _u32.keybd_event(k, 0, 0, 0)
    time.sleep(0.03)
    for k in reversed(keys): _u32.keybd_event(k, 0, 2, 0)

def key_ctrl(key="", text=""):
    if text:
        safe = text.replace("'", "''")
        ps = f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{safe}')"
        subprocess.run(list(("powershell", "-NoProfile", "-Command", ps)), capture_output=True, creationflags=_NO_WIN)
        return f"⌨️ Text gesendet: **{text[:30]}**"
    combos = {
        "alttab": (0x12, 0x09), "newtab": (0x11, 0x54), "closetab": (0x11, 0x57),
        "nexttab": (0x11, 0x09), "reopentab": (0x11, 0x10, 0x54), "snapleft": (0x5B, 0x25),
        "snapright": (0x5B, 0x27), "desknext": (0x11, 0x5B, 0x27), "deskprev": (0x11, 0x5B, 0x25),
        "snip": (0x5B, 0x10, 0x53), "copy": (0x11, 0x43), "paste": (0x11, 0x56), "undo": (0x11, 0x5A)
    }
    if key in combos: _combo(*combos[key]); return f"⚡ Shortcut **{key}** ausgeführt."
    vks = {"enter": 0x0D, "esc": 0x1B, "space": 0x20, "tab": 0x09, "back": 0x08, "f5": 0x74, "f11": 0x7A, "j": 0x4A, "k": 0x4B, "l": 0x4C, "f": 0x46, "c": 0x43}
    if key in vks: _combo(vks[key]); return f"⌨️ Taste **{key.upper()}** gedrückt."
    return ""

def app_window(action, target=""):
    tl = (target or "").strip().lower()
    if action == "close" and tl:
        cnt = 0
        for p in psutil.process_iter(list(("name",))):
            if tl in (p.info.get("name") or "").lower():
                try: p.terminate(); cnt += 1
                except Exception: pass
        return f"❌ **{target}** beendet ({cnt})." if cnt else f"❓ **{target}** läuft nicht."
    if action in ("min", "max"):
        sw = 6 if action == "min" else 3
        found = list()
        def cb(hwnd, _):
            buf = ctypes.create_unicode_buffer(256); _u32.GetWindowTextW(hwnd, buf, 256)
            if _u32.IsWindowVisible(hwnd) and buf.value and (not tl or tl in buf.value.lower()): found.append(hwnd)
            return True
        _u32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
        hwnd = next(iter(found), 0) if tl else _u32.GetForegroundWindow()
        if hwnd: _u32.ShowWindow(hwnd, sw); return f"🪟 Fenster {'minimiert' if action=='min' else 'maximiert'}."
    return "❓ Fenster nicht gefunden."

def get_bt_devices():
    try:
        ps = "Get-PnpDevice -Class Bluetooth | Where-Object { $_.FriendlyName -and $_.FriendlyName -notmatch 'Adapter|Enumerator|RFCOMM|Protocol|Transport|Microsoft' } | ForEach-Object { $_.FriendlyName + '|' + $_.Status }"
        r = subprocess.run(list(("powershell", "-NoProfile", "-Command", ps)), capture_output=True, text=True, timeout=6, creationflags=_NO_WIN)
        res = list()
        for ln in (r.stdout or "").splitlines():
            if "|" in ln: n, s = ln.split("|", 1); res.append({"name": n.strip(), "ok": s.strip() == "OK"})
        return res
    except Exception: return list()

def bluetooth_ctrl(action, dev=""):
    d = (dev or "").strip()
    if action == "list" or not d:
        devs = get_bt_devices()
        return "🔵 **Bluetooth-Geräte:**\n" + "\n".join(f"• {x['name']} ({'Aktiv' if x['ok'] else 'Getrennt'})" for x in devs) if devs else "🔵 Keine Bluetooth-Geräte gefunden."
    state = "Enable" if action == "on" else "Disable"
    ps = f"Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.FriendlyName -like '*{d}*' }} | {state}-PnpDevice -Confirm:$false"
    subprocess.run(list(("powershell", "-NoProfile", "-Command", ps)), capture_output=True, timeout=8, creationflags=_NO_WIN)
    return f"🔵 Bluetooth (**{'Verbunden' if action=='on' else 'Getrennt'}**) für **{d}**!"

def mjpeg_stream():
    from PIL import Image
    try:
        import mss
        with mss.mss() as sct:
            mon = sct.monitors.item(1) if hasattr(sct.monitors, "item") else next(itertools.islice(sct.monitors, 1, 2))
            while True:
                raw = sct.grab(mon)
                im = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX").resize((800, 450))
                buf = io.BytesIO(); im.save(buf, format="JPEG", quality=42)
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.getvalue() + b"\r\n")
                time.sleep(0.03)
    except Exception:
        from PIL import ImageGrab
        while True:
            im = ImageGrab.grab().resize((800, 450))
            buf = io.BytesIO(); im.save(buf, format="JPEG", quality=42)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.getvalue() + b"\r\n")
            time.sleep(0.035)

def get_live_jpeg():
    from PIL import ImageGrab
    im = ImageGrab.grab().resize((800, 450))
    buf = io.BytesIO(); im.save(buf, format="JPEG", quality=42); buf.seek(0)
    return buf
