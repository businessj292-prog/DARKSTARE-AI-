@echo off
title DARKSTARE AI v2.0
color 0A
setlocal EnableDelayedExpansion

echo.
echo  ============================================================
echo    DARKSTARE AI TRADING BRAIN v2.0
echo    Claude + GPT-4o  ^|  Live Forex, Gold, News, MT5
echo  ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────
python --version >nul 2>&1
if not %errorlevel%==0 (
    echo  [ERROR] Python not installed.
    echo.
    echo  Download Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: Tick "Add Python to PATH" during install!
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b
)

for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  [OK] %PYVER% found

:: ── Install packages ──────────────────────────────────────────────────
echo  [..] Installing packages if needed...
pip install fastapi uvicorn httpx --quiet --no-warn-script-location 2>nul
echo  [OK] Packages ready

:: ── Create desktop shortcut ───────────────────────────────────────────
echo  [..] Creating desktop shortcut...
python "%~dp0make_shortcut.py" "%~f0" 2>nul

:: ── Get local IP for mobile ───────────────────────────────────────────
set LOCAL_IP=localhost
for /f "usebackq" %%I in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*'} | Select-Object -First 1).IPAddress" 2^>nul`) do (
    set LOCAL_IP=%%I
)

:: ── Start server ──────────────────────────────────────────────────────
echo  [..] Starting DarkStare AI server...
start "DarkStare Server" /MIN python "%~dp0server.py"

echo  [..] Waiting for server to start...
timeout /t 4 /nobreak >nul

:: ── Open browser ──────────────────────────────────────────────────────
echo  [..] Opening browser...
start "" "http://localhost:8000"

echo.
echo  ============================================================
echo   DarkStare AI is RUNNING
echo.
echo   Desktop: http://localhost:8000
echo   Mobile:  http://!LOCAL_IP!:8000
echo.
echo   SETUP (first time):
echo    1. Click the gear icon (CFG) in the sidebar
echo    2. Enter your API keys
echo    3. Click SAVE ALL KEYS
echo    4. Click TEST next to each key
echo    5. Go to DASH and click ANALYZE NOW
echo.
echo   MOBILE: Open http://!LOCAL_IP!:8000 on your phone
echo    iPhone:  Share button -> Add to Home Screen
echo    Android: Menu (3 dots) -> Add to Home Screen
echo  ============================================================
echo.
echo  Server is running in background.
echo  Close this window when done.
echo.
pause
