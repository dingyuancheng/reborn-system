@echo off
chcp 65001 >nul
cd /d %~dp0api
echo.
echo ================================
echo   Reborn System - API 启动
echo ================================
echo.
call %~dp0venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause