@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ML-Based Attendance System (v4.0)
echo ========================================
echo.

:: 1. Hard Reset - Clean up existing processes
echo [1/4] Performing Hard Reset...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo [+] Clean-up complete.

:: 2. Start Backend
echo.
echo [2/4] Starting Backend Server...
start "Attendance Backend" /D "%~dp0server" cmd /c "python app.py"

:: Wait for Backend to be ready (Max 30 seconds)
echo Waiting for Backend (Port 5000) to respond...
set /a count=0
:wait_backend
set /a count+=1
if %count% gtr 30 (
    echo [X] Backend failed to start in time.
    pause
    exit /b 1
)
powershell -Command "$c = New-Object System.Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1', 5000); if ($c.Connected) { $c.Close(); exit 0 } } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    <nul set /p=.
    timeout /t 1 /nobreak >nul
    goto wait_backend
)
echo.
echo [+] Backend is UP!

:: 3. Open Browser
echo.
echo [3/3] Opening Monolithic Portal at http://localhost:5000
start "" http://localhost:5000

echo.
echo ========================================
echo   SYSTEM READY - MONOLITHIC MODE
echo ========================================
echo.
pause
endlocal
