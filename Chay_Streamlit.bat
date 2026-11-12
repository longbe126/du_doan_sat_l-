@echo off
chcp 65001 >nul
title Trung Tam Giam Sat Nguy Co Sat Lo Dat (Streamlit)
cd /d "%~dp0"
echo =================================================================
echo   TRUNG TAM GIAM SAT NGUY CO SAT LO DAT (STREAMLIT DASHBOARD)
echo =================================================================
echo Dang kiem tra du lieu, mo hinh AI va khoi dong giao dien Streamlit...
echo Trinh duyet se tu dong mo tai: http://localhost:8501
echo.
set "PY_CMD=python"
if exist ".\.venv\Scripts\python.exe" (
    set "PY_CMD=.\.venv\Scripts\python.exe"
) else if exist ".\venv\Scripts\python.exe" (
    set "PY_CMD=.\venv\Scripts\python.exe"
)

if not exist "data\landslide.db" (
    echo [*] Khoi tao co so du lieu SQLite...
    "%PY_CMD%" init_database.py
)
if not exist "models\logistic_regression.pkl" (
    echo [*] Huan luyen 3 mo hinh AI...
    "%PY_CMD%" app\core\train_models.py
)

"%PY_CMD%" -m streamlit run streamlit_app.py
pause
