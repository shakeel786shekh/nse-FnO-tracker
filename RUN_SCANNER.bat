@echo off
title Trade With Brain — F&O Scanner
color 0A

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   Trade With Brain — F&O Scanner v2.0        ║
echo ║   Angel One SmartAPI                         ║
echo ╚══════════════════════════════════════════════╝
echo.

:: Scanner folder mein jao
cd /d "D:\Trade With Brain\Trade With Brain\Scanner"

:: Python check karo
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nahi mila! Python install karo.
    pause
    exit
)

echo ✅ Python found!
echo.
echo Choose scan mode:
echo   1. Single scan - ek baar
echo   2. Auto scan - har 30 min
echo   3. Auto scan - har 60 min
echo.
set /p choice="Enter 1, 2 or 3: "

if "%choice%"=="1" (
    echo.
    echo 🔍 Single scan shuru ho raha hai...
    python master_scanner.py --once
)
if "%choice%"=="2" (
    echo.
    echo 🤖 Auto scan shuru ho raha hai - har 30 min...
    python master_scanner.py --interval 30
)
if "%choice%"=="3" (
    echo.
    echo 🤖 Auto scan shuru ho raha hai - har 60 min...
    python master_scanner.py --interval 60
)

echo.
echo ✅ Scan complete! Obsidian mein 03-Watchlist folder check karo.
pause
