# Starts the SmartWait backend and opens Google Chrome directly
$url = "http://127.0.0.1:8000/"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"

if (Test-Path $chrome) {
    Start-Process $chrome -ArgumentList $url
} else {
    Start-Process "chrome.exe" -ArgumentList $url -ErrorAction SilentlyContinue
}

Set-Location "$PSScriptRoot"
& "smartwait\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --app-dir "smartwait\backend" --host 127.0.0.1 --port 8000
