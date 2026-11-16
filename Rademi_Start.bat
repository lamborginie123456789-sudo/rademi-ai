@echo off 
title RADEMI AI - Lokaler PC-Motor 
cd /d "C:\Users\maart" 
if not exist "rademi-ai" git clone https://github.com 
cd /d "C:\Users\maart\rademi-ai" 
git pull 
pip install -q flask psutil pillow qrcode websockets pycaw comtypes llama-cpp-python 
start "" "https://github.io" 
pythonw rademi.py
