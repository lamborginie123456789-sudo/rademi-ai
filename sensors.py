import glob
import time
import socket
import subprocess
import psutil

NO_WIN = 0x08000000

def init_lhm_dll():
    try:
        import clr
        muster = r"C:\Users\maart\AppData\Local\Microsoft\WinGet\**\*LibreHardwareMonitorLib.dll"
        treffer = glob.glob(muster, recursive=True)
        if not treffer:
            treffer = glob.glob(r"C:\Program Files*\**\*LibreHardwareMonitorLib.dll", recursive=True)
        if not treffer:
            return None
        clr.AddReference(next(iter(treffer)))
        from LibreHardwareMonitor.Hardware import Computer
        comp = Computer()
        comp.IsCpuEnabled = True
        comp.IsMotherboardEnabled = True
        comp.IsControllerEnabled = True
        comp.IsGpuEnabled = True
        comp.IsStorageEnabled = True
        comp.IsBatteryEnabled = True
        comp.Open()
        return comp
    except Exception:
        return None

def read_wmi_fans():
    fans = []
    try:
        cmd = "Get-CimInstance -ClassName Win32_Fan -ErrorAction SilentlyContinue | ForEach-Object { if ($_.DesiredSpeed) { \"$($_.Name)|$($_.DesiredSpeed)\" } }"
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], creationflags=NO_WIN, text=True, stderr=subprocess.DEVNULL).strip()
        for line in out.splitlines():
            if "|" in line:
                name, rpm = line.split("|", 1)
                if rpm.strip().isdigit() and int(rpm.strip()) > 0:
                    val = int(rpm.strip())
                    fans.append({"name": name.strip() or "System-Lüfter", "rpm": val, "pct": min(100, int(val / 50))})
    except Exception:
        pass
    return fans

def read_lhm_all(comp):
    res = {"cpu_temp": None, "core_temps": [], "cpu_watt": 0.0, "fans": [], "sensors": []}
    if comp is not None:
        try:
            from LibreHardwareMonitor.Hardware import HardwareType, SensorType
            for hw in comp.Hardware:
                hw.Update()
                for sub in hw.SubHardware:
                    sub.Update()
                    for s in sub.Sensors:
                        if s.Value is not None and s.SensorType == SensorType.Fan and float(s.Value) > 0:
                            v = float(s.Value)
                            res["fans"].append({"name": s.Name, "rpm": int(round(v)), "pct": min(100, int(v / 50))})

                ssd_temp_gefunden = False
                for s in hw.Sensors:
                    if s.Value is None:
                        continue
                    val = float(s.Value)
                    if hw.HardwareType == HardwareType.Cpu:
                        if s.SensorType == SensorType.Temperature and 10.0 <= val <= 115.0:
                            name_l = (s.Name or "").lower()
                            if any(k in name_l for k in ["package", "tctl", "tdie", "average"]):
                                res["cpu_temp"] = val
                            elif "core" in name_l:
                                res["core_temps"].append({"name": s.Name, "temp": round(val, 1)})
                                if res["cpu_temp"] is None:
                                    res["cpu_temp"] = val
                        elif s.SensorType == SensorType.Power and "package" in (s.Name or "").lower():
                            res["cpu_watt"] = round(val, 1)
                    elif s.SensorType == SensorType.Fan and val > 0:
                        res["fans"].append({"name": f"{hw.Name} ({s.Name})", "rpm": int(round(val)), "pct": min(100, int(val / 50))})
                    elif hw.HardwareType == HardwareType.Storage and s.SensorType == SensorType.Temperature and not ssd_temp_gefunden:
                        if 15.0 <= val <= 80.0 and "limit" not in (s.Name or "").lower() and "warning" not in (s.Name or "").lower():
                            res["sensors"].append({"name": hw.Name, "val": f"{int(round(val))} °C", "sub": "NVMe Temperatur"})
                            ssd_temp_gefunden = True
        except Exception:
            pass

    if not res["fans"]:
        res["fans"] = read_wmi_fans()

    try:
        bat = psutil.sensors_battery()
        if bat is not None:
            status = "Netzbetrieb" if bat.power_plugged else "Akkubetrieb"
            res["sensors"].append({"name": "Laptop Akku", "val": f"{int(bat.percent)} %", "sub": status})
    except Exception:
        pass
    return res

def check_ping():
    t0 = time.monotonic()
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.6):
            return int((time.monotonic() - t0) * 1000), True
    except Exception:
        return -1, False

def build_alerts(c_temp, g_temp, ram_pct, disk_pct, ping_ms, online):
    warns = []
    if isinstance(c_temp, (int, float)) and c_temp >= 85:
        warns.append({"level": "danger", "msg": f"Hohe CPU-Temperatur: {int(c_temp)} °C"})
    if isinstance(g_temp, (int, float)) and g_temp >= 85:
        warns.append({"level": "danger", "msg": f"Hohe GPU-Temperatur: {int(g_temp)} °C"})
    if ram_pct >= 90:
        warns.append({"level": "warn", "msg": f"Kritische RAM-Auslastung: {ram_pct:.1f} %"})
    if disk_pct >= 90:
        warns.append({"level": "warn", "msg": f"Wenig freier Speicher auf C:\\ ({disk_pct:.1f} % belegt)"})
    if not online:
        warns.append({"level": "danger", "msg": "Keine Internetverbindung erkannt"})
    elif ping_ms >= 150:
        warns.append({"level": "warn", "msg": f"Hohe Netzwerk-Latenz: {ping_ms} ms"})
    return warns
