@echo off
chcp 65001 >nul
cd /d %~dp0mobile_h5
echo.
echo ================================
echo   Reborn System - App 启动
echo ================================
echo.
npm run dev
pause