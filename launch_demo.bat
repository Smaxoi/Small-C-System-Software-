@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
python demo_new_features.py
echo.
echo =========================================
echo   現在啟動互動式直譯器，請試試 LIST 和 MEMSHOW
echo =========================================
echo.
python main.py
pause
