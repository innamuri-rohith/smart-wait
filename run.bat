@echo off
setlocal
cd /d "%~dp0"
echo Launching SmartWait interactive website in Google Chrome...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:8000/"
echo Starting SmartWait API server...
smartwait\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir smartwait\backend --host 127.0.0.1 --port 8000
pause
