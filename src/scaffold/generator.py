"""
ScaffoldGenerator — Orchestrates complete creation of autonomous agent projects from templates.
"""
import json
import shutil
from pathlib import Path
from typing import Any, Optional

from .validator import ScaffoldValidator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"


class ScaffoldGenerator:
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR

    def generate(
        self,
        name: str,
        agent_type: str = "react",
        skills: Optional[list[str]] = None,
        model: str = "gemini-2.5-flash-lite",
        fallback_model: str = "openai/gpt-4o",
        output_dir: str = "..",
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Generates a complete, autonomous agent project in `output_dir / name`.
        """
        ScaffoldValidator.validate_project_name(name)
        ScaffoldValidator.validate_agent_type(agent_type)
        
        target_dir = (Path(output_dir) / name).resolve()
        ScaffoldValidator.validate_output_directory(target_dir, force=force)

        # Ensure selected skills are valid
        type_meta = self.get_template_meta(agent_type)
        default_skills = type_meta.get("default_skills", ["researcher", "tester"])
        selected_skills = ScaffoldValidator.validate_skills(skills) if skills else default_skills

        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create project metadata file
        project_meta = {
            "name": name,
            "type": agent_type,
            "model": model,
            "fallback_model": fallback_model,
            "skills": selected_skills,
            "ui_enabled": False,
            "ui_port": 7860,
            "has_memory": True,
        }
        with open(target_dir / "_meta.json", "w", encoding="utf-8") as f:
            json.dump(project_meta, f, indent=2)

        # 2. Copy core codebase structure from repo root as the react template base
        self._scaffold_code_base(target_dir, project_meta)

        # 3. Create run launchers
        self._generate_launchers(target_dir, name)

        # 4. Create pyproject.toml and config files
        self._generate_configs(target_dir, project_meta)

        # 5. Create .agent directory structure
        (target_dir / ".agent").mkdir(exist_ok=True)

        return {
            "status": "success",
            "project_name": name,
            "path": str(target_dir),
            "type": agent_type,
            "skills": selected_skills,
            "model": model,
            "fallback_model": fallback_model,
            "ui_enabled": False
        }

    def get_template_meta(self, agent_type: str) -> dict[str, Any]:
        meta_file = self.templates_dir / agent_type / "_meta.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "type": agent_type,
            "description": f"{agent_type} agent",
            "default_skills": ["researcher", "tester"]
        }

    def _scaffold_code_base(self, target_dir: Path, meta: dict[str, Any]) -> None:
        """Copies src/ and config/ from repo_root into target_dir."""
        src_target = target_dir / "src"
        config_target = target_dir / "config"
        tests_target = target_dir / "tests"

        # Copy src directory excluding __pycache__
        if (REPO_ROOT / "src").exists():
            shutil.copytree(
                REPO_ROOT / "src",
                src_target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                dirs_exist_ok=True
            )

        # Copy config directory excluding __pycache__
        if (REPO_ROOT / "config").exists():
            shutil.copytree(
                REPO_ROOT / "config",
                config_target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                dirs_exist_ok=True
            )

        # Copy tests directory excluding __pycache__
        if (REPO_ROOT / "tests").exists():
            shutil.copytree(
                REPO_ROOT / "tests",
                tests_target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                dirs_exist_ok=True
            )

    def _generate_launchers(self, target_dir: Path, name: str) -> None:
        run_bat = f"""@echo off
setlocal enabledelayedexpansion
title {name} — 1-Click Launcher

echo ==================================================
echo   🚀 {name.upper()} — 1-CLICK LAUNCHER
echo ==================================================

:: Detect python executable
set PYTHON_CMD=python
if exist ".venv\\Scripts\\python.exe" (
    set PYTHON_CMD=.venv\\Scripts\\python.exe
) else if exist "..\\agent-builder\\.venv\\Scripts\\python.exe" (
    set PYTHON_CMD=..\\agent-builder\\.venv\\Scripts\\python.exe
)

if "%~1"=="--resume" (
    %PYTHON_CMD% -m src.main --resume
    goto END
)

if "%~1"=="" (
    if exist ".agent\\state.json" (
        echo.
        echo [i] Une session precedente en attente a ete detectee.
        set /p CHOICE="Voulez-vous reprendre la session precedente ? (O/N) : "
        if /i "!CHOICE!"=="O" (
            %PYTHON_CMD% -m src.main --resume
            goto END
        )
    )
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
%PYTHON_CMD% -m src.main "!TASK!"

:END
echo.
echo ==================================================
echo   Execution terminee.
echo ==================================================
"""
        run_sh = f"""#!/bin/bash
PYTHON_CMD="python3"
if [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -d "../agent-builder/.venv" ]; then
    PYTHON_CMD="../agent-builder/.venv/bin/python"
fi

$PYTHON_CMD -m src.main "$@"
"""

        with open(target_dir / "run.bat", "w", encoding="utf-8") as f:
            f.write(run_bat)
        with open(target_dir / "run.sh", "w", encoding="utf-8") as f:
            f.write(run_sh)

    def _generate_configs(self, target_dir: Path, meta: dict[str, Any]) -> None:
        # Update agent_config.json
        config_file = target_dir / "config" / "agent_config.json"
        config_data = {
            "model": meta["model"],
            "fallback_model": meta["fallback_model"],
            "temperature": 0.2,
            "max_tokens_per_session": 500000,
            "max_consecutive_iterations": 15,
            "system_prompt_path": "config/system_prompt.md",
            "ui_enabled": meta.get("ui_enabled", False),
            "ui_port": meta.get("ui_port", 7860)
        }
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # Create pyproject.toml
        pyproject_content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{meta['name']}"
version = "0.1.0"
description = "Autonomous Agent generated by Agentic Builder SDK"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.25.0",
    "tenacity>=8.2.0",
    "google-genai>=0.1.0",
    "openai>=1.0.0",
]

[project.optional-dependencies]
ui = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0"
]
"""
        with open(target_dir / "pyproject.toml", "w", encoding="utf-8") as f:
            f.write(pyproject_content)

        # Create .env.example
        env_content = """GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
"""
        with open(target_dir / ".env.example", "w", encoding="utf-8") as f:
            f.write(env_content)

        # Create README.md
        readme_content = f"""# {meta['name']}

Generated by **Agentic Builder SDK**.

## Type
`{meta['type']}`

## Quick Start
```bash
# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env

# Run agent
run.bat "Your task instruction here"
```
"""
        with open(target_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
