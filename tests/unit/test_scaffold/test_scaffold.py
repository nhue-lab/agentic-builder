import json
import pytest
from pathlib import Path

from src.scaffold.validator import ScaffoldValidator
from src.scaffold.generator import ScaffoldGenerator
from src.scaffold.patcher import ProjectPatcher


def test_validator_project_name():
    ScaffoldValidator.validate_project_name("valid_name-123")
    with pytest.raises(ValueError):
        ScaffoldValidator.validate_project_name("invalid name!")
    with pytest.raises(ValueError):
        ScaffoldValidator.validate_project_name("")


def test_validator_agent_type():
    ScaffoldValidator.validate_agent_type("react")
    ScaffoldValidator.validate_agent_type("bot")
    with pytest.raises(ValueError):
        ScaffoldValidator.validate_agent_type("unknown_type")


def test_validator_skills():
    cleaned = ScaffoldValidator.validate_skills(["RESEARCHER", " tester "])
    assert cleaned == ["researcher", "tester"]
    with pytest.raises(ValueError):
        ScaffoldValidator.validate_skills(["unknown_skill"])


def test_generator_new_project(tmp_path):
    generator = ScaffoldGenerator()
    res = generator.generate(
        name="test_agent",
        agent_type="react",
        skills=["researcher", "tester"],
        model="gemini-2.5-flash-lite",
        fallback_model="openai/gpt-4o",
        output_dir=str(tmp_path),
        force=True
    )

    assert res["status"] == "success"
    project_dir = tmp_path / "test_agent"
    assert project_dir.exists()
    assert (project_dir / "_meta.json").exists()
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "run.bat").exists()

    with open(project_dir / "_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["name"] == "test_agent"
    assert meta["type"] == "react"
    assert "researcher" in meta["skills"]


def test_patcher_add_skill_and_ui(tmp_path):
    generator = ScaffoldGenerator()
    generator.generate(
        name="patch_agent",
        agent_type="react",
        skills=["researcher"],
        output_dir=str(tmp_path),
        force=True
    )
    project_dir = tmp_path / "patch_agent"

    patcher = ProjectPatcher(project_dir)

    # 1. Add skill
    res_skill = patcher.add_skill("git_push")
    assert res_skill["status"] == "success"
    assert "git_push" in res_skill["skills"]

    # Add same skill again (idempotent)
    res_repeat = patcher.add_skill("git_push")
    assert res_repeat["status"] == "already_exists"

    # 2. Add UI
    res_ui = patcher.add_ui(port=8080)
    assert res_ui["status"] == "success"
    assert res_ui["ui_port"] == 8080

    with open(project_dir / "_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["ui_enabled"] is True
    assert meta["ui_port"] == 8080
    assert "git_push" in meta["skills"]

    # 3. Set model
    res_model = patcher.set_model("gemini-2.5-pro", "openai/gpt-4o")
    assert res_model["status"] == "success"
    assert res_model["model"] == "gemini-2.5-pro"
