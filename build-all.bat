@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "PROJECTS=admin_web mobile_app mobile_h5"
set "FAILED=0"

echo ============================================
echo   Reborn System - 批量打包 Vue 项目
echo ============================================
echo.

for %%P in (%PROJECTS%) do call :build_one "%%P"

cd /d "%ROOT%"
echo ============================================
if "%FAILED%"=="0" (
    echo   全部打包完成！
) else (
    echo   部分项目打包失败，请检查上方日志
)
echo ============================================
pause
endlocal
exit /b

:build_one
set "PROJ=%~1"
echo --------------------------------------------
echo [%PROJ%] 开始打包...
echo --------------------------------------------
cd /d "%ROOT%%PROJ%"
if not exist package.json (
    echo [%PROJ%] 未找到 package.json，跳过
    echo.
    exit /b
)
if not exist node_modules (
    echo [%PROJ%] 未找到 node_modules，正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo [%PROJ%] 依赖安装失败！
        set "FAILED=1"
        echo.
        exit /b
    )
)
set "BUILD_CMD=build"
if "%PROJ%"=="mobile_app" set "BUILD_CMD=build:h5"
echo [%PROJ%] 执行命令: npm run %BUILD_CMD%
echo.
call npm run %BUILD_CMD%
if errorlevel 1 (
    echo [%PROJ%] 打包失败！
    set "FAILED=1"
) else (
    echo [%PROJ%] 打包完成 -^> %ROOT%%PROJ%\dist
)
echo.
exit /b