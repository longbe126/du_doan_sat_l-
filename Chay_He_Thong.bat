@echo off
chcp 65001 >nul
title Trung Tam Giam Sat Nguy Co Sat Lo Dat
cd /d "%~dp0"
echo =================================================================
echo   TRUNG TAM GIAM SAT NGUY CO SAT LO DAT (3D + AI INTELLIGENCE)
echo =================================================================
echo Dang khoi dong may chu backend FastAPI va giao dien React 3D...
echo Trinh duyet se tu dong mo tai: http://localhost:8000
echo.
if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_app.py
) else if exist ".\venv\Scripts\python.exe" (
    ".\venv\Scripts\python.exe" run_app.py
) else (
    python run_app.py
)
pause
