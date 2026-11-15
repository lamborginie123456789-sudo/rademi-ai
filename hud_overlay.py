import threading, tkinter as tk
import hardware

_hud = None

def toggle_hud():
    global _hud
    if _hud is not None:
        try: _hud.destroy()
        except Exception: pass
        _hud = None
        return False
    def _run():
        global _hud
        root = tk.Tk()
        _hud = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.88)
        root.configure(bg="#090d18", highlightbackground="#38bdf8", highlightthickness=1)
        root.geometry("250x185+20+20")
        def s_drag(e): root._dx, root._dy = e.x, e.y
        def d_drag(e): root.geometry(f"+{root.winfo_x()+e.x-root._dx}+{root.winfo_y()+e.y-root._dy}")
        def close():
            global _hud
            _hud = None
            root.destroy()
        hdr = tk.Frame(root, bg="#0f172a", height=24); hdr.pack(fill="x")
        lt = tk.Label(hdr, text=" ● HARDWARE TELEMETRIE", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 8, "bold")); lt.pack(side="left", padx=4)
        tk.Button(hdr, text="✕", fg="#94a3b8", bg="#0f172a", bd=0, font=("Segoe UI", 8, "bold"), command=close).pack(side="right", padx=6)
        for w in (hdr, lt): w.bind("<Button-1>", s_drag); w.bind("<B1-Motion>", d_drag)
        body = tk.Frame(root, bg="#090d18", padx=10, pady=6); body.pack(fill="both", expand=True)
        rows = dict()
        for k, name in (("cpu","CPU"),("ctemp","CPU TEMP"),("gpu","GPU"),("vram","VRAM"),("ram","RAM"),("net","NETZWERK")):
            f = tk.Frame(body, bg="#090d18"); f.pack(fill="x", pady=2)
            tk.Label(f, text=name, fg="#94a3b8", bg="#090d18", font=("Segoe UI", 8)).pack(side="left")
            v = tk.Label(f, text="--", fg="#f8fafc", bg="#090d18", font=("Consolas", 8, "bold")); v.pack(side="right")
            rows[k] = v
        def upd():
            if _hud is None: return
            try:
                d = hardware.get_telemetrie()
                rows["cpu"].config(text=f"{d.get('cpu_pct',0)}% · {d.get('cpu_mhz',0)} MHz")
                ct = d.get("cpu_temp", 0)
                rows["ctemp"].config(text=f"{ct} °C", fg=("#ef4444" if ct >= 90 else "#eab308" if ct >= 75 else "#22c55e"))
                rows["gpu"].config(text=f"{d.get('gpu_pct',0)}% · {d.get('gpu_temp',0)} °C")
                rows["vram"].config(text=f"{d.get('vram_used',0)}/{d.get('vram_tot',0)} GB")
                rows["ram"].config(text=f"{d.get('ram_used',0)}/{d.get('ram_tot',0)} GB ({d.get('ram_pct',0)}%)")
                rows["net"].config(text=f"⬇{d.get('net_down',0)} ⬆{d.get('net_up',0)} MB/s")
            except Exception: pass
            root.after(1000, upd)
        upd()
        root.mainloop()
        _hud = None
    threading.Thread(target=_run, daemon=True).start()
    return True
