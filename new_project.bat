@echo off
setlocal enabledelayedexpansion
title Agentic Builder — New Project Creator

echo ==================================================
echo   ✨ CREATION D'UN NOUVEAU PROJET AGENTIC BUILDER
echo ==================================================
echo.

if "%~1"=="" (
    set /p PNAME="Entrez le nom de votre nouveau projet (ex: mon-agent) : "
) else (
    set PNAME=%~1
)

if "!PNAME!"=="" (
    echo [!] Aucun nom de projet fourni. Annulation.
    pause
    exit /b 1
)

echo.
echo [>] Generation du projet dans ../!PNAME! ...
echo.

python scripts/create_project.py "../!PNAME!"

echo.
echo ==================================================
echo   Creation terminee. Appuyez sur une touche.
echo ==================================================
pause
