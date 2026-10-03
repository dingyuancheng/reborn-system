@echo off
chcp 65001 >nul
echo ============================================
echo   构建前端 + 同步到 Android 工程
echo ============================================
echo.

cd /d "%~dp0"

echo [0/2] 清理 Android 构建缓存...
set "APK_DIR=%cd%\android\app\build\outputs\apk\debug"
if exist "%APK_DIR%" (
    echo   删除 %APK_DIR%
    del /q "%APK_DIR%\*.*" 2>nul
) else (
    echo   目录不存在，跳过清理
)
echo.

echo [1/2] 构建前端...
call npm run build:android
if errorlevel 1 (
    echo.
    echo [错误] 前端构建失败！
    pause
    exit /b 1
)
echo.

echo [2/2] 同步到 Android 工程...
call npx cap sync
if errorlevel 1 (
    echo.
    echo [错误] Capacitor 同步失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   完成！可以去 Android Studio 打包 APK 了
echo ============================================
pause