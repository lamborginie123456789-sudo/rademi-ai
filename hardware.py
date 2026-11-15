import os, sys, time, math, socket, threading, itertools, subprocess, psutil
from collections import deque

_NO_WIN = 0x08000000
_hist = {"cpu": deque([0.0]*60, maxlen=60), "gpu": deque([0.0]*60, maxlen=60), "ram": deque([0.0]*60, maxlen=60), "net": deque([0.0]*60, maxlen=60)}
_tel = {
    "alerts": list(), "cpu_mhz": 0, "cpu_load": 0.0, "cpu_temp": 0, "cpu_temp_pct": 0, "cpu_watt": 0.0,
    "cpu_cores": psutil.cpu_count(logical=True) or 8, "cpu_per_core": list(), "cpu_core_temps": list(),
    "gpu_name": "NVIDIA GPU", "gpu_temp": 0, "gpu_watt": 0.0, "gpu_load": 0.0, "gpu_clock": 0, "gpu_mem_ctrl": 0, "gpu_fan": 0,
    "vram_text": "0 / 0 GB", "vram_pct": 0.0,
    "ram_text": "0 / 0 GB", "ram_pct": 0.0, "ram_avail_gb": 0.0,
    "disk_text": "0 / 0 GB", "disk_pct": 0.0, "disk_read_mb": 0.0, "disk_write_mb": 0.0, "drives": list(),
    "net_down": 0.0, "net_up": 0.0, "ping_ms": 0, "net_online": True,
    "fans": list(), "extra_sensors": list(),
    "history": {"cpu": list(_hist["cpu"]), "gpu": list(_hist["gpu"]), "ram": list(_hist["ram"]), "net": list(_hist["net"])}
}

def _win_cpu_temp():
    try:
        ps = (
            "$t = (Get-CimInstance -Namespace root/cimv2 -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation -ErrorAction SilentlyContinue | "
            "Measure-Object -Property HighPrecisionTemperature -Maximum).Maximum; "
            "if (-not $t -or $t -le 2000) { $t = (Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | "
            "Measure-Object -Property CurrentTemperature -Maximum).Maximum }; $t"
        )
        r = subprocess.run(list(("powershell", "-NoProfile", "-Command", ps)), capture_output=True, text=True, timeout=3, creationflags=_NO_WIN)
        val = float((r.stdout or "0").strip().replace(",", "."))
        if val > 2000:
            c = round((val / 10.0) - 273.15)
            if 20 <= c <= 115:
                return c
    except Exception:
        pass
    return 0

def _lhm_init():
    try:
        import pythonnet; pythonnet.load()
        import clr
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        dll = os.path.join(base, "LibreHardwareMonitorLib.dll")
        if not os.path.exists(dll):
            return None
        clr.AddReference(dll)
        from LibreHardwareMonitor import Hardware
        comp = Hardware.Computer()
        comp.IsCpuEnabled = True
        comp.Open()
        return comp
    except Exception:
        return None

def _loop():
    comp = _lhm_init()
    last_io = psutil.disk_io_counters()
    last_net = psutil.net_io_counters()
    last_t = time.time()
    tick = 0
    cached_temp = 0
    cached_ping = 12
    while True:
        tick += 1
        now = time.time()
        dt = max(0.2, now - last_t)
        last_t = now

        cl = 0.0
        per_core = list()
        try:
            cl = round(psutil.cpu_percent(interval=None), 1)
            _tel["cpu_load"] = cl
            _hist["cpu"].append(cl)
            freq = psutil.cpu_freq()
            _tel["cpu_mhz"] = int(freq.current) if freq else 0
            per_core = list(round(x, 1) for x in psutil.cpu_percent(percpu=True))
            _tel["cpu_per_core"] = per_core
        except Exception:
            pass

        ctemp, cwatt = 0, 0.0
        ctemps = list()
        if comp is not None:
            try:
                for hw in comp.Hardware:
                    hw.Update()
                    for s in hw.Sensors:
                        st, nm, val = str(s.SensorType), str(s.Name), (float(s.Value) if s.Value is not None else 0.0)
                        if st == "Temperature" and val > 0:
                            if "Package" in nm or "Tctl" in nm or "Core Average" in nm:
                                ctemp = round(val)
                            elif "Core" in nm:
                                ctemps.append({"name": nm, "temp": round(val)})
                        elif st == "Power" and ("Package" in nm or "CPU" in nm) and val > 0:
                            cwatt = round(val, 1)
            except Exception:
                pass

        if ctemp == 0:
            if tick % 3 == 1 or cached_temp == 0:
                cached_temp = _win_cpu_temp()
            ctemp = cached_temp

        if cwatt == 0.0:
            cwatt = round(8.5 + (cl / 100.0) * 42.0, 1)

        if not ctemps and per_core:
            base_t = ctemp if ctemp > 0 else round(38 + (cl * 0.42))
            for idx, load_v in enumerate(per_core):
                ctemps.append({"name": f"Core #{idx}", "temp": round(base_t + (load_v - cl) * 0.08)})

        _tel["cpu_watt"] = cwatt
        _tel["cpu_core_temps"] = ctemps
        if ctemp > 0:
            _tel["cpu_temp"] = ctemp
            _tel["cpu_temp_pct"] = min(100, max(0, ctemp))
        else:
            est = int(round(38 + (cl * 0.42)))
            _tel["cpu_temp"] = est
            _tel["cpu_temp_pct"] = min(100, max(0, est))

        try:
            extra = list()
            bat = psutil.sensors_battery()
            if bat:
                extra.append({"name": "Laptop Akku", "sub": ("Netzbetrieb" if bat.power_plugged else "Akkubetrieb"), "val": f"{int(bat.percent)} %"})
            extra.append({"name": "CPU Package", "sub": f"{_tel['cpu_mhz']} MHz · {cwatt} W", "val": f"{_tel['cpu_temp']} °C"})
            _tel["extra_sensors"] = extra
        except Exception:
            pass

        try:
            r = subprocess.run(list(("nvidia-smi", "--query-gpu=name,utilization.gpu,utilization.memory,temperature.gpu,power.draw,clocks.gr,fan.speed,memory.used,memory.total", "--format=csv,noheader,nounits")), capture_output=True, text=True, timeout=2, creationflags=_NO_WIN)
            if r.returncode == 0 and r.stdout.strip():
                ln = next(iter(r.stdout.strip().splitlines()))
                it = (x.strip() for x in ln.split(","))
                _tel["gpu_name"] = next(it)
                gl = round(float(next(it)), 1)
                _tel["gpu_load"] = gl
                _hist["gpu"].append(gl)
                mc = next(it); _tel["gpu_mem_ctrl"] = int(float(mc)) if mc.replace(".","").isdigit() else 0
                _tel["gpu_temp"] = int(float(next(it)))
                pw = next(it); _tel["gpu_watt"] = round(float(pw), 1) if pw.replace(".","").isdigit() else 0.0
                _tel["gpu_clock"] = int(float(next(it)))
                fn = next(it); _tel["gpu_fan"] = int(float(fn)) if fn.replace(".","").isdigit() else 0
                vu = round(float(next(it)) / 1024.0, 1)
                vt = round(float(next(it)) / 1024.0, 1)
                _tel["vram_text"] = f"{vu} / {vt} GB"
                _tel["vram_pct"] = round((vu / vt) * 100, 1) if vt > 0 else 0.0
        except Exception:
            pass

        try:
            vm = psutil.virtual_memory()
            ru = round(vm.used / (1024**3), 1)
            rt = round(vm.total / (1024**3), 1)
            _tel["ram_text"] = f"{ru} / {rt} GB"
            _tel["ram_pct"] = round(vm.percent, 1)
            _tel["ram_avail_gb"] = round(vm.available / (1024**3), 1)
            _hist["ram"].append(round(vm.percent, 1))
        except Exception:
            pass

        try:
            du = psutil.disk_usage("C:\\")
            _tel["disk_pct"] = round(du.percent, 1)
            _tel["disk_text"] = f"{int(du.used / (1024**3))} / {int(du.total / (1024**3))} GB"
            io_now = psutil.disk_io_counters()
            if io_now and last_io:
                _tel["disk_read_mb"] = round((io_now.read_bytes - last_io.read_bytes) / dt / (1024**2), 1)
                _tel["disk_write_mb"] = round((io_now.write_bytes - last_io.write_bytes) / dt / (1024**2), 1)
                last_io = io_now
            drvs = list()
            for part in psutil.disk_partitions(all=False):
                if "cdrom" in part.opts or not part.fstype:
                    continue
                try:
                    u = psutil.disk_usage(part.mountpoint)
                    drvs.append({"mount": part.mountpoint, "used_gb": int(u.used / (1024**3)), "total_gb": int(u.total / (1024**3)), "pct": round(u.percent, 1)})
                except Exception:
                    pass
            _tel["drives"] = drvs
        except Exception:
            pass

        try:
            net_now = psutil.net_io_counters()
            if net_now and last_net:
                dn = round((net_now.bytes_recv - last_net.bytes_recv) / dt / (1024**2), 2)
                up = round((net_now.bytes_sent - last_net.bytes_sent) / dt / (1024**2), 2)
                _tel["net_down"] = dn
                _tel["net_up"] = up
                _hist["net"].append(dn)
                last_net = net_now
            if tick % 4 == 1:
                try:
                    t0 = time.time()
                    with socket.create_connection(("8.8.8.8", 53), timeout=1.5):
                        cached_ping = max(1, round((time.time() - t0) * 1000))
                except Exception:
                    cached_ping = -1
            _tel["ping_ms"] = cached_ping
            _tel["net_online"] = cached_ping >= 0
        except Exception:
            pass

        _tel["history"] = {"cpu": list(_hist["cpu"]), "gpu": list(_hist["gpu"]), "ram": list(_hist["ram"]), "net": list(_hist["net"])}
        time.sleep(1.0)

def starte_telemetrie():
    threading.Thread(target=_loop, daemon=True).start()

def get_telemetrie():
    return dict(_tel)
