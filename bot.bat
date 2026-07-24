@echo off
title Agentic Builder — Telegram Bot Launcher

echo ==================================================
echo   🤖 AGENTIC BUILDER — TELEGRAM BOT 24/7 LAUNCHER
echo ==================================================

if not exist ".venv\Scripts\python.exe" (
    echo [!] Environnement virtuel non trouve.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo [>] Démarrage du bot Telegram en mode Polling...
echo.
python src/main.py --mode telegram

pause
