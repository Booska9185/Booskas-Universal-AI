@echo off
title Booska RPG System Orchestrator
:menu
cls
echo ===================================================
echo          BOOSKA RPG SYSTEM ORCHESTRATOR           
echo ===================================================
echo.
echo    [R] - Launch / Hot-Restart Overlay
echo    [K] - Force Kill Running Overlay
echo    [Q] - Close This Manager
echo.
echo ===================================================
set /p choice="Select an action: "

if /i "%choice%"=="R" goto restart
if /i "%choice%"=="K" goto kill
if /i "%choice%"=="Q" goto end
goto menu

:restart
echo.
echo [System]: Hunting down and killing active tracking instances...
taskkill /fi "WINDOWTITLE eq BooskaInstance*" /t /f >nul 2>&1
timeout /t 1 >nul
echo [System]: Spawning decoupled overlay interface...
:: The 'start' command decouples the process from this terminal window completely
start "BooskaInstance" python overlay.py
echo [System]: Overlay running independently! Returning to menu...
timeout /t 2 >nul
goto menu

:kill
echo.
echo [System]: Forcefully evicting overlay environment...
taskkill /fi "WINDOWTITLE eq BooskaInstance*" /t /f >nul 2>&1
echo [System]: Active instances cleared.
timeout /t 2 >nul
goto menu

:end
exit