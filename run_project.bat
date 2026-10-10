@echo off
title UPSKILL AI - Launcher
color 0A

echo =====================================================================
echo                UPSKILL AI - Starting Application
echo =====================================================================
echo.

:: Detect project directory location
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
if exist "%PROJECT_DIR%\Sih-ai-Learning-Platform-main\backend" (
    set "PROJECT_DIR=%PROJECT_DIR%\Sih-ai-Learning-Platform-main"
)

set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

:: Validate directories exist
if not exist "%BACKEND_DIR%" (
    color 0C
    echo [ERROR] Backend folder not found at: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    color 0C
    echo [ERROR] Frontend folder not found at: %FRONTEND_DIR%
    pause
    exit /b 1
)

echo [1/3] Starting Backend API (FastAPI) on http://127.0.0.1:8000 ...
if exist "%BACKEND_DIR%\.venv\Scripts\activate.bat" (
    start "UPSKILL AI - Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) else (
    start "UPSKILL AI - Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
)

echo [2/3] Starting Frontend (React / Vite) on http://localhost:5173 ...
start "UPSKILL AI - Frontend (React)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo [3/3] Opening browser in 4 seconds...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo =====================================================================
echo  Application is running!
echo.
echo  - Frontend:  http://localhost:5173
echo  - Backend:   http://127.0.0.1:8000
echo  - API Docs:  http://127.0.0.1:8000/docs
echo.
echo  Demo Credentials:
echo    Email:    demo@statlearn.local
echo    Password: Demo@12345
echo.
echo  To stop the servers, simply close the two command windows.
echo =====================================================================
echo.
pause
