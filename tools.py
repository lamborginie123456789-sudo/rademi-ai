import os
import io
import time
import base64
import subprocess
import contextlib
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

NO_WIN = 0x08000000
whisper = None
image_pipe = None

def lade_audio_modell():
    global whisper
    whisper = WhisperModel("tiny", device="cpu", compute_type="int8")

def get_image_pipe():
    global image_pipe
    if image_pipe is None:
        import torch
        from diffusers import AutoPipelineForText2Image
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        dt = torch.float16 if dev == "cuda" else torch.float32
        image_pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=dt,
            variant="fp16" if dev == "cuda" else None
        ).to(dev)
    return image_pipe

def bild_erstellen(prompt):
    res = get_image_pipe()(prompt=prompt, num_inference_steps=2, guidance_scale=0.0)
    img = next(iter(res.images))
    fn = f"bild_{int(time.time())}.png"
    img.save(fn)
    with open(fn, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return fn, b64

def ps_run(cmd):
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            stderr=subprocess.STDOUT,
            creationflags=NO_WIN,
            text=True,
            encoding="cp850",
            errors="replace"
        )
        return out.strip() or "Befehl ausgeführt."
    except subprocess.CalledProcessError as e:
        return f"Fehler:\n{e.output}"

def py_run(code_str):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(code_str, globals())
        return buf.getvalue().strip() or "Python-Code ausgeführt."
    except Exception as e:
        return f"Python-Fehler:\n{e}"

def audio_aufnehmen(sek=5):
    while whisper is None:
        time.sleep(0.2)
    auf = sd.rec(int(sek * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    write("temp.wav", 16000, auf)
    segs, _ = whisper.transcribe("temp.wav", language="de")
    txt = " ".join([s.text for s in segs]).strip()
    if os.path.exists("temp.wav"):
        os.remove("temp.wav")
    return txt
