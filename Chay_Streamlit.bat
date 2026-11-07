@echo off
title Trung Tam Giam Sat Nguy Co Sat Lo Dat (Streamlit)
cd /d "D:\Landslide_Risk_System"
echo =================================================================
echo   TRUNG TAM GIAM SAT NGUY CO SAT LO DAT (STREAMLIT DASHBOARD)
echo =================================================================
echo Dang khoi dong giao dien Streamlit...
echo Trinh duyet se tu dong mo tai: http://localhost:8501
echo.
if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else if exist ".\venv\Scripts\python.exe" (
    ".\venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else (
    python -m streamlit run streamlit_app.py
)
pause
