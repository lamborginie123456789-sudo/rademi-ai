import os, time, json, math, sqlite3, threading, subprocess
import hardware

DB = r"C:\Users\maart\Desktop\KI\rademi.db"
_NO_WIN = 0x08000000
_notes = list()

def add_note(lvl, msg):
    _notes.insert(0, {"ts": time.strftime("%H:%M:%S"), "lvl": lvl, "msg": msg})
    del _notes[25:]

def get_notes(): return list(_notes)

def start_temp_logger():
    def _loop():
        while True:
            try:
                t = hardware.get_telemetrie()
                with sqlite3.connect(DB) as c:
                    c.execute("CREATE TABLE IF NOT EXISTS temp_log (ts INTEGER, cpu REAL, gpu REAL)")
                    c.execute("INSERT INTO temp_log VALUES (?, ?, ?)", (int(time.time()), t.get("cpu_temp", 0), t.get("gpu_temp", 0)))
                if t.get("cpu_temp", 0) >= 92: add_note("warn", f"CPU-Temperatur hoch: {t['cpu_temp']} °C")
                if t.get("gpu_temp", 0) >= 85: add_note("warn", f"GPU-Temperatur hoch: {t['gpu_temp']} °C")
            except Exception: pass
            time.sleep(60)
    threading.Thread(target=_loop, daemon=True).start()

def get_win_errors():
    try:
        ps = "$t=(Get-Date).AddHours(-24); Get-WinEvent -FilterHashtable @{LogName='System','Application';Level=1,2;StartTime=$t} -MaxEvents 10 -ErrorAction SilentlyContinue | Where-Object { $_.Message -notmatch 'pythonw\.exe' } | Select-Object -First 5 | ForEach-Object { $_.TimeCreated.ToString('dd.MM. HH:mm') + ' | ' + $_.ProviderName + ': ' + ($_.Message -replace '\\r|\\n',' ').Substring(0, [Math]::Min(140, $_.Message.Length)) }"
        r = subprocess.run(list(("powershell","-NoProfile","-Command",ps)), capture_output=True, text=True, timeout=8, creationflags=_NO_WIN)
        return (r.stdout or "").strip() or "Keine aktuellen kritischen Windows-Fehler in den letzten 24 Stunden gefunden."
    except Exception as e:
        return f"Ereignisprotokoll konnte nicht gelesen werden: {e}"

def read_screen_ocr():
    img = r"C:\Users\maart\Desktop\KI\last_screen.png"
    try:
        ps = (
            f"Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
            f"$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            f"$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height);"
            f"$g=[System.Drawing.Graphics]::FromImage($bmp);$g.CopyFromScreen(0,0,0,0,$b.Size);"
            f"$bmp.Save('{img}');"
            f"Add-Type -AssemblyName System.Runtime.WindowsRuntime;"
            f"[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]|Out-Null;"
            f"[Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]|Out-Null;"
            f"$s=[System.IO.File]::OpenRead('{img}');$ras=[System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($s);"
            f"$dec=[Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($ras).GetAwaiter().GetResult();"
            f"$sb=$dec.GetSoftwareBitmapAsync().GetAwaiter().GetResult();"
            f"$eng=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages();"
            f"$res=$eng.RecognizeAsync($sb).GetAwaiter().GetResult();$res.Text"
        )
        r = subprocess.run(list(("powershell","-NoProfile","-Command",ps)), capture_output=True, text=True, timeout=10, creationflags=_NO_WIN)
        return (r.stdout or "").strip()
    except Exception:
        return ""

def run_benchmark():
    t0 = time.perf_counter()
    s = 0.0
    for i in range(1, 3500000): s += math.sqrt(i) * math.sin(i)
    dt = round(time.perf_counter() - t0, 2)
    score = int(10000 / max(0.1, dt))
    tel = hardware.get_telemetrie()
    add_note("info", f"Benchmark abgeschlossen: {score} Punkte")
    return f"🏁 **CPU-Kurzbenchmark fertig:**\n• Zeit: **{dt} Sek.**\n• Score: **{score} Punkte**\n• CPU-Temp: **{tel.get('cpu_temp')} °C** | GPU-Temp: **{tel.get('gpu_temp')} °C**"
