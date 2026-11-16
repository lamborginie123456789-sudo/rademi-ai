@echo off 
schtasks /run /tn "RademiKI" >nul 2>&1 
start "" "http://127.0.0.1:5005"
