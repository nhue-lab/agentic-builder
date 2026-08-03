"""
ScaffoldValidator — Validation helpers for project generation and patching parameters.
"""
import re
from pathlib import Path

VALID_TYPES = ["react", "bot", "pipeline", "api"]
VALID_SKILLS = ["researcher", "tester", "git_push", "subagent", "ui"]

NAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

class ScaffoldValidator:
    @staticmethod
    def validate_project_name(name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty.")
        if not NAME_REGEX.match(name):
            raise ValueError(f"Invalid project name '{name}'. Use only letters, numbers, underscores, or hyphens.")

    @staticmethod
    def validate_agent_type(agent_type: str) -> None:
        if agent_type not in VALID_TYPES:
            raise ValueError(f"Invalid agent type '{agent_type}'. Must be one of: {', '.join(VALID_TYPES)}")

    @staticmethod
    def validate_skills(skills: list[str]) -> list[str]:
        cleaned = [s.strip().lower() for s in skills if s and s.strip()]
        for s in cleaned:
            if s not in VALID_SKILLS:
                raise ValueError(f"Unknown skill '{s}'. Available skills: {', '.join(VALID_SKILLS)}")
        return cleaned

    @staticmethod
    def validate_output_directory(target_path: Path, force: bool = False) -> None:
        if target_path.exists() and any(target_path.iterdir()):
            if not force:
                raise FileExistsError(
                    f"Target directory '{target_path}' already exists and is not empty. Use --force to overwrite."
                )
