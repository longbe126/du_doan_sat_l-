@echo off
chcp 65001 >nul
title Day Ma Nguon Len GitHub (longbe126/du_doan_sat_l-)
cd /d "%~dp0"
echo =================================================================
echo   DAY MA NGUON DA SUA LOI LEN GITHUB (longbe126/du_doan_sat_l-)
echo =================================================================
if not exist ".git" (
    git init
    git branch -M main
    git remote add origin https://github.com/longbe126/du_doan_sat_l-.git
)
git add -A
git commit -m "Fix Streamlit UI/UX, navigation, timeline playback, map selection, GIS slope formula, and ML evaluation pipeline"
echo.
echo Dang day len GitHub (nhanh main)...
git push -u origin main
echo.
echo =================================================================
echo   HOAN TAT!
echo =================================================================
pause
