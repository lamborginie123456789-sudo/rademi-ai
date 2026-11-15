import time, tkinter as tk

root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg="black", cursor="none")
root.focus_force()

start_ts = time.time()
last_xy = [root.winfo_pointerx(), root.winfo_pointery()]

def _wake(e=None):
    if time.time() - start_ts > 0.6:
        root.destroy()

def _poll_mouse():
    cur = [root.winfo_pointerx(), root.winfo_pointery()]
    if abs(cur[0] - last_xy[0]) > 4 or abs(cur[1] - last_xy[1]) > 4:
        _wake()
        return
    root.after(120, _poll_mouse)

root.bind("<Key>", _wake)
root.bind("<Button>", _wake)
root.after(700, _poll_mouse)
root.mainloop()
