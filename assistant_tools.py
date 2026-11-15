import os, glob, json, ssl, platform, subprocess, itertools, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
import psutil, hardware

_last_city = ""
_ssl = ssl._create_unverified_context()
_NO_WIN = 0x08000000
WMO = {0:("☀️","Klar"),1:("🌤️","Heiter"),2:("⛅","Wolkig"),3:("☁️","Bedeckt"),45:("🌫️","Nebel"),51:("🌦️","Niesel"),61:("🌧️","Regen"),63:("🌧️","Regen"),71:("🌨️","Schnee"),80:("🌦️","Schauer"),95:("⛈️","Gewitter")}
TZ = {"herzberg":("Herzberg (Elster)",1),"berlin":("Berlin",1),"deutschland":("Deutschland",1),"polen":("Polen",1),"warschau":("Warschau",1),"frankreich":("Paris",1),"spanien":("Madrid",1),"italien":("Rom",1),"wien":("Wien",1),"schweiz":("Zürich",1),"london":("London",0),"england":("London",0),"tokio":("Tokio",9),"japan":("Tokio",9),"sydney":("Sydney",11),"australien":("Sydney",11),"dubai":("Dubai",4),"moskau":("Moskau",3),"china":("Peking",8),"kalifornien":("Kalifornien (LA)",-8),"los angeles":("Los Angeles",-8),"la":("Los Angeles",-8),"new york":("New York",-5),"usa":("New York",-5)}
LOKAL_ORTE = (
    {"name":"Herzberg (Elster), Brandenburg","lat":51.6917,"lon":13.2356,"de":True},
    {"name":"Danna, Niedergörsdorf (Brandenburg)","lat":51.9942,"lon":12.9694,"de":True},
    {"name":"Niedergörsdorf, Teltow-Fläming (Brandenburg)","lat":51.9767,"lon":12.9869,"de":True},
    {"name":"Jüterbog, Teltow-Fläming (Brandenburg)","lat":51.9911,"lon":13.0819,"de":True},
    {"name":"Falkenberg/Elster, Brandenburg","lat":51.5844,"lon":13.2417,"de":True},
    {"name":"Luckenwalde, Brandenburg","lat":52.0886,"lon":13.1689,"de":True},
    {"name":"Berlin, Deutschland","lat":52.5200,"lon":13.4050,"de":True},
)

def _dst(dt):
    y = dt.year
    m, o = datetime(y,3,31,1,tzinfo=timezone.utc), datetime(y,10,31,1,tzinfo=timezone.utc)
    return (m - timedelta(days=(m.weekday()+1)%7)) <= dt < (o - timedelta(days=(o.weekday()+1)%7))

def re_clean(s): return "".join(c if c.isalnum() or c==" " else " " for c in s.lower())

def _get(u):
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=4, context=_ssl).read().decode("utf-8"))
    except Exception:
        raw = subprocess.check_output(list(("curl.exe","-s","-L","--max-time","5",u)), text=True, timeout=7, creationflags=_NO_WIN)
        return json.loads(raw)

def get_time_card(q):
    global _last_city
    utc = datetime.now(timezone.utc)
    eu = 2 if _dst(utc) else 1
    loc = utc + timedelta(hours=eu)
    qc = " " + re_clean(q) + " "
    zn, zo, hit = "Herzberg (Elster)", eu, False
    for k, (n, b) in TZ.items():
        if f" {k} " in qc and k != "herzberg":
            _last_city, zn, hit = k, n, True
            zo = b + (1 if (_dst(utc) and b in (-8,-5,0,1,2)) else 0); break
    if not hit and any(w in qc for w in (" dort "," da ")) and _last_city in TZ:
        n, b = TZ[_last_city]; zn, zo = n, b + (1 if (_dst(utc) and b in (-8,-5,0,1,2)) else 0)
    tgt = utc + timedelta(hours=zo)
    dh = zo - eu
    dd = "Gestern" if tgt.date() < loc.date() else ("Morgen" if tgt.date() > loc.date() else "Heute")
    return {"is_single":(zn=="Herzberg (Elster)"),"local_ort":"Herzberg (Elster)","local_tz":f"UTC+{eu}","local_time":loc.strftime("%H:%M:%S"),"local_date":loc.strftime("%d.%m.%Y"),"local_pct":round(((loc.hour*60+loc.minute)/1440)*100,1),"local_day":6<=loc.hour<20,"target_ort":zn,"target_tz":f"UTC{zo:+.1f}".replace(".0",""),"target_time":tgt.strftime("%H:%M:%S"),"target_date":tgt.strftime("%d.%m.%Y"),"target_pct":round(((tgt.hour*60+tgt.minute)/1440)*100,1),"target_day":6<=tgt.hour<20,"diff":"Gleiche Zeit" if dh==0 else f"{dh:+.1f}".replace(".0","")+" Std.","day_diff":dd}

def search_cities(q):
    res, seen, cq = list(), set(), " ".join(q.replace("/"," ").replace(","," ").split())
    low_q = cq.lower()
    for lo_item in LOKAL_ORTE:
        if any(w in lo_item["name"].lower() for w in low_q.split() if len(w)>=3):
            seen.add((round(lo_item["lat"],2), round(lo_item["lon"],2)))
            res.append(lo_item)
    such = list((cq,)) + list(w for w in cq.split() if len(w)>=3)
    for t in such:
        try:
            for r in (_get(f"https://open-meteo.com{urllib.parse.quote(t)}&count=5&language=de&format=json").get("results") or list()):
                k = (round(r["latitude"],2), round(r["longitude"],2))
                if k not in seen: seen.add(k); res.append({"name":f"{r['name']}, {r.get('admin1','')} ({r.get('country','')})".replace(",  ("," ("),"lat":r["latitude"],"lon":r["longitude"],"de":r.get("country_code")=="DE"})
        except Exception: pass
    res.sort(key=lambda x: x["de"], reverse=True)
    return list(itertools.islice(res, 6))

def get_weather_by_coords(lat, lon, ort):
    try:
        w = _get(f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset&timezone=Europe%2FBerlin&forecast_days=5")
        c, d = w["current"], w["daily"]
        ic, ds = WMO.get(c.get("weather_code",0), ("🌤️","Wechselhaft"))
        tage = list({"date":f"{t[8:10]}.{t[5:7]}.","icon":WMO.get(wc,("🌤️","")),"min":round(mn),"max":round(mx),"rain":rn or 0} for t,wc,mn,mx,rn in zip(d.get("time",list()),d.get("weather_code",list()),d.get("temperature_2m_min",list()),d.get("temperature_2m_max",list()),d.get("precipitation_probability_max",list())))
        sr, ss = next(iter(d.get("sunrise") or list()),""), next(iter(d.get("sunset") or list()),"")
        return {"ort":ort,"icon":ic,"desc":ds,"temp":round(c["temperature_2m"],1),"feels":round(c["apparent_temperature"],1),"hum":c["relative_humidity_2m"],"wind":round(c["wind_speed_10m"],1),"press":int(round(c.get("surface_pressure",1013))),"sunrise":sr[11:16] if len(sr)>=16 else "--:--","sunset":ss[11:16] if len(ss)>=16 else "--:--","days":tage}
    except Exception:
        return {"ort":ort,"icon":"⛅","desc":"Offline-Daten","temp":8.5,"feels":6.5,"hum":74,"wind":12.0,"press":1014,"sunrise":"07:32","sunset":"16:18","days":list(({"date":"Heute","icon":"⛅","min":4,"max":9,"rain":15},))}

def get_weather_card(city="Herzberg"):
    cl = city.strip()
    if not cl or any(w in cl.lower() for w in ("bei mir","hier","herzberg","herzber")): return {"type":"weather","data":get_weather_by_coords(51.6917,13.2356,"Herzberg (Elster), Brandenburg")}
    tr = search_cities(cl)
    if len(tr) == 1: t = next(iter(tr)); return {"type":"weather","data":get_weather_by_coords(t["lat"],t["lon"],t["name"])}
    return {"type":"picker","query":cl,"options":tr}

def launch_windows_app(app):
    q = app.lower().strip(" .!?\"'")
    uris = {"whatsapp":"whatsapp:","spotify":"spotify:","rechner":"ms-calculator:","einstellungen":"ms-settings:","store":"ms-windows-store:","xbox":"xbox:","mail":"outlookmail:","kalender":"outlookcal:","kamera":"microsoft.windows.camera:"}
    for k, u in uris.items():
        if k in q:
            try: os.startfile(u); return f"✅ Ich habe **{k.capitalize()}** gestartet!"
            except Exception: pass
    for m in (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\**\*.lnk", os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\**\*.lnk")):
        for l in glob.glob(m, recursive=True):
            if q in os.path.basename(l).lower():
                try: os.startfile(l); return f"✅ Ich habe **{os.path.splitext(os.path.basename(l))}** geöffnet!"
                except Exception: pass
    res = subprocess.run(list(("powershell","-NoProfile","-Command",f"$a=Get-StartApps|Where-Object{{$_.Name -like '*{q}*'}}|Select-Object -First 1;if($a){{Start-Process('shell:AppsFolder\\'+$a.AppID);$a.Name}}")), capture_output=True, text=True, timeout=6, creationflags=_NO_WIN)
    if res.stdout.strip(): return f"✅ Ich habe **{res.stdout.strip()}** gestartet!"
    try: subprocess.Popen(q, shell=True, creationflags=_NO_WIN); return f"✅ Startbefehl für **{app}** ausgeführt."
    except Exception as e: return f"❌ Konnte **{app}** nicht starten ({e})."

def get_specs_card():
    t, r = hardware.get_telemetrie(), psutil.virtual_memory()
    return {"pc":platform.node(),"os":f"{platform.system()} {platform.release()}","cpu":platform.processor() or "CPU","cores":f"{psutil.cpu_count(logical=False)} Kerne / {psutil.cpu_count(logical=True)} Threads","cpu_temp":t["cpu_temp"],"cpu_load":t["cpu_load"],"gpu":t["gpu_name"],"gpu_temp":t["gpu_temp"],"vram":t["vram_text"],"ram_total":f"{round(r.total/(1024**3),1)} GB","ram_pct":r.percent,"drives":t["drives"]}
