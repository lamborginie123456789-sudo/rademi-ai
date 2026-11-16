@echo off
title RADEMI AI - PC-Motor
echo Starte RADEMI AI Einrichtung...
where python >nul 2>nul || winget install --id Python.Python.3.11 -e --silent --accept-package-agreements
where git >nul 2>nul || winget install --id Git.Git -e --silent --accept-package-agreements
cd /d "%USERPROFILE%"
if not exist "rademi-ai" git clone https://github.com
cd /d "%USERPROFILE%\rademi-ai"
git pull
pip install -q flask psutil pillow qrcode websockets pycaw comtypes llama-cpp-python
start "" "https://github.io"
start "" pythonw rademi.py
exit
