"""
ProjectPatcher — Incremental modification engine for existing scaffolded projects.
Supports adding skills, enabling UI, and changing models.
"""
import json
from pathlib import Path
from typing import Any, Optional

from .validator import ScaffoldValidator


class ProjectPatcher:
    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir).resolve()
        self.meta_path = self.project_dir / "_meta.json"
        self.config_path = self.project_dir / "config" / "agent_config.json"

        if not self.project_dir.exists():
            raise FileNotFoundError(f"Project directory '{self.project_dir}' does not exist.")
        if not self.meta_path.exists():
            raise FileNotFoundError(
                f"Invalid project at '{self.project_dir}': missing '_meta.json'. "
                "Ensure this is a project scaffolded with Agentic Builder."
            )

    def _load_meta(self) -> dict[str, Any]:
        with open(self.meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_meta(self, data: dict[str, Any]) -> None:
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self, data: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_skill(self, skill_name: str) -> dict[str, Any]:
        cleaned_skill = ScaffoldValidator.validate_skills([skill_name])[0]
        meta = self._load_meta()
        current_skills = meta.get("skills", [])

        if cleaned_skill in current_skills:
            return {
                "status": "already_exists",
                "message": f"Skill '{cleaned_skill}' is already present in project.",
                "skills": current_skills
            }

        current_skills.append(cleaned_skill)
        meta["skills"] = current_skills
        self._save_meta(meta)

        return {
            "status": "success",
            "message": f"Skill '{cleaned_skill}' successfully added to project.",
            "skills": current_skills
        }

    def add_ui(self, port: int = 7860) -> dict[str, Any]:
        meta = self._load_meta()
        config = self._load_config()

        meta["ui_enabled"] = True
        meta["ui_port"] = port
        config["ui_enabled"] = True
        config["ui_port"] = port

        self._save_meta(meta)
        self._save_config(config)

        return {
            "status": "success",
            "message": f"UI dashboard enabled on port {port}.",
            "ui_enabled": True,
            "ui_port": port
        }

    def set_model(self, model: str, fallback_model: Optional[str] = None) -> dict[str, Any]:
        meta = self._load_meta()
        config = self._load_config()

        meta["model"] = model
        config["model"] = model

        if fallback_model:
            meta["fallback_model"] = fallback_model
            config["fallback_model"] = fallback_model

        self._save_meta(meta)
        self._save_config(config)

        return {
            "status": "success",
            "message": f"Model updated to '{model}'.",
            "model": model,
            "fallback_model": meta.get("fallback_model")
        }
