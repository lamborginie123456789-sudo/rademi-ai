@echo off
title RADEMI AI
set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "%PY%" winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
if not exist "%PY%" set "PY=python"
cd /d "%USERPROFILE%"
if exist "rademi-ai" rmdir /s /q "rademi-ai"
curl -L "https://github.com" -o r.zip
tar -xf r.zip
ren "rademi-ai-main" "rademi-ai"
del r.zip
cd /d "%USERPROFILE%\rademi-ai"
"%PY%" -m pip install flask psutil pillow qrcode websockets pycaw comtypes llama-cpp-python
start "" "https://github.io"
"%PY%" rademi.py
pause
