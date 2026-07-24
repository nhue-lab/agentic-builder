@echo off
setlocal enabledelayedexpansion
title Agentic Builder — 1-Click Launcher

echo ==================================================
echo   🚀 AGENTIC BUILDER — 1-CLICK LAUNCHER
echo ==================================================

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [!] Environnement virtuel non trouve. Installation...
    uv venv .venv
    call .venv\Scripts\activate.bat
    pip install -e .
) else (
    call .venv\Scripts\activate.bat
)

:: Check if state exists for resume
if exist ".agent\state.json" (
    echo.
    echo [i] Une session precedente /grill-me en attente a ete detectee.
    set /p CHOICE="Voulez-vous reprendre la session precedente ? (O/N) : "
    if /i "!CHOICE!"=="O" (
        python src/main.py --resume
        goto END
    )
)

echo.
if "%~1"=="" (
    set /p TASK="Entrez la tache a executer par l'agent : "
) else (
    set TASK=%~1
)

if "!TASK!"=="" (
    echo [!] Aucune tache entree. Annulation.
    pause
    exit /b 1
)

echo.
echo [>] Lancement de l'agent pour la tache : "!TASK!"
echo.
python src/main.py "!TASK!"

:END
echo.
echo ==================================================
echo   Execution terminee. Appuyez sur une touche.
echo ==================================================
pause
