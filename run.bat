@echo off
chcp 65001 >nul
title AI SHORTS FACTORY AND YOUTUBE MANAGER - LAUNCHER
color 0A

echo ==============================================================================
echo        AI SHORTS FACTORY AND YOUTUBE MANAGER - AUTONOMOUS SYSTEM
echo ==============================================================================
echo.

REM 1. Chuyen toi thu muc goc cua project
cd /d "%~dp0"

REM 2. Kiem tra Python
echo [*] 1/5. Kiem tra moi truong Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Python chua duoc cai dat hoac chua duoc them vao PATH!
    pause
    exit /b 1
)
python --version

REM 3. Kiem tra va tu dong khoi dong OLLAMA neu co
echo.
echo [*] 2/5. Kiem tra dich vu Ollama AI (Local LLM)...
set "OLLAMA_CMD="
where ollama >nul 2>&1 && set "OLLAMA_CMD=ollama"
if not defined OLLAMA_CMD if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_CMD=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_CMD if exist "C:\Program Files\Ollama\ollama.exe" set "OLLAMA_CMD=C:\Program Files\Ollama\ollama.exe"

if defined OLLAMA_CMD (
    echo [+] Tim thay Ollama tai: %OLLAMA_CMD%
    tasklist /fi "imagename eq ollama.exe" 2>nul | findstr /i "ollama.exe" >nul
    if errorlevel 1 (
        echo [*] Dang tu dong khoi dong Ollama serve trong background...
        start "" /b "%OLLAMA_CMD%" serve
        timeout /t 3 >nul
    )
    echo [OK] Ollama da duoc kich hoat va san sang tai http://127.0.0.1:11434 !
)

if not defined OLLAMA_CMD (
    echo [i] Chu y: May chua cai dat Ollama local.
    echo     - Ban co the tai Ollama tai: https://ollama.com/
    echo     - Hoac dung Cloud AI: He thong se tu dong dung Gemini hoac OpenAI trong file .env!
)

REM 4. Kiem tra va cai dat thu vien Backend
echo.
echo [*] 3/5. Kiem tra thu vien Backend (requirements.txt)...
python -m pip install -r backend/requirements.txt --quiet
echo [OK] Thu vien Backend da san sang!

REM 5. Khoi tao thu muc assets va am thanh mac dinh
echo.
echo [*] 4/5. Khoi tao thu vien am thanh va assets mac dinh...
python backend/scripts/generate_default_assets.py

REM 6. Kiem tra Frontend Dist
echo.
echo [*] 5/5. Kiem tra giao dien Frontend...
if not exist "frontend\dist" (
    echo [*] Tien hanh build Frontend lan dau...
    cd frontend
    call npm install --quiet
    call npm run build
    cd ..
)
echo [OK] Frontend da san sang!

REM 7. Tu dong mo trinh duyet vao Dashboard sau 3 giay
start "" /b cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000"

REM 8. Khoi dong Backend FastAPI Server
echo.
echo ==============================================================================
echo [*] HE THONG DA KHOI DONG THANH CONG!
echo [*] Giao dien Studio: http://127.0.0.1:8000
echo [*] Tai lieu API:     http://127.0.0.1:8000/docs
echo [*] Nhan Ctrl + C de dung he thong.
echo ==============================================================================
echo.

python backend/run_backend.py

pause
