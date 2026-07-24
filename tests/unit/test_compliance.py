import os
import inspect
from src.context.state import AgentState, AgentStatus, LLMDecision
from src.lms.base_client import BaseLLMClient
from src.harness.skills.base_skill import BaseSkill

def test_no_typescript_files():
    # Make sure no TS or JS remains in workspace (except node_modules which will be deleted later)
    for root, dirs, files in os.walk("."):
        if "node_modules" in root or "dist" in root or ".git" in root or ".gemini" in root or ".venv" in root or "venv" in root:
            continue
        for file in files:
            assert not file.endswith(".ts"), f"TypeScript file found: {os.path.join(root, file)}"
            assert not file.endswith(".js"), f"JavaScript file found: {os.path.join(root, file)}"

def test_file_structure_compliance():
    expected_files = [
        "pyproject.toml",
        "config/settings.py",
        "config/mcp_servers.json",
        "src/main.py",
        "src/context/state.py",
        "src/lms/base_client.py",
        "src/lms/router.py",
        "src/prompt/formatter.py",
        "src/harness/mcp_client.py",
        "src/harness/skills/base_skill.py",
        "src/harness/skills/researcher/skill.py",
        "src/loop/engine.py",
        "src/loop/router.py",
        "src/telemetry/logger.py",
        "src/telemetry/metrics.py"
    ]
    for rel_path in expected_files:
        assert os.path.exists(rel_path), f"Required file missing from plan: {rel_path}"

def test_contracts_compliance():
    # 1. AgentState Attributes
    state_sig = inspect.signature(AgentState)
    expected_state_fields = [
        "session_id", "status", "current_agent", "history", 
        "injected_skills", "errors", "iteration", "max_iterations", "metadata"
    ]
    for field in expected_state_fields:
        assert field in AgentState.model_fields, f"AgentState missing required field: {field}"

    # 2. BaseLLMClient interface
    assert hasattr(BaseLLMClient, "generate"), "BaseLLMClient missing abstract method: generate"
    assert inspect.iscoroutinefunction(BaseLLMClient.generate), "BaseLLMClient.generate must be an async coroutine"

    # 3. BaseSkill interface
    assert hasattr(BaseSkill, "name"), "BaseSkill missing abstract property: name"
    assert hasattr(BaseSkill, "description"), "BaseSkill missing abstract property: description"
    assert hasattr(BaseSkill, "execute"), "BaseSkill missing abstract method: execute"
    assert inspect.iscoroutinefunction(BaseSkill.execute), "BaseSkill.execute must be an async coroutine"
