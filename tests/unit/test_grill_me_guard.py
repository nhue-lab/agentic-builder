import pytest
import os
import json
from unittest.mock import AsyncMock, patch
from src.context.state import AgentState, AgentStatus
from src.harness.guardrails.grill_me_guard import GrillMeGuard
from src.loop.hitl.impact_report import ImpactReport
from config.settings import settings

@pytest.mark.asyncio
async def test_grill_me_guard_disabled(clean_state):
    with patch("config.settings.settings.grill_me_enabled", False):
        state = await GrillMeGuard.intercept("My task", clean_state)
        assert state.status == AgentStatus.IDLE

@pytest.mark.asyncio
async def test_grill_me_guard_approved(clean_state):
    clean_state.status = AgentStatus.GRILL_ME_APPROVED
    with patch("config.settings.settings.grill_me_enabled", True):
        state = await GrillMeGuard.intercept("My task", clean_state)
        assert state.status == AgentStatus.RUNNING

@pytest.mark.asyncio
async def test_grill_me_guard_intercept_and_save(clean_state):
    report_path = ".agent/impact_report.json"
    if os.path.exists(report_path):
        os.remove(report_path)

    mock_report = ImpactReport(
        objective="Create a new task handler",
        files_affected=["src/task.py"],
        risks=["potential error"],
        guardrails=["sandbox"]
    )
    
    mock_response = AsyncMock()
    mock_response.content = mock_report.model_dump_json()

    with patch("src.lms.router.llm_router.generate", return_value=mock_response) as mock_gen, \
         patch("config.settings.settings.grill_me_enabled", True):
        
        state = await GrillMeGuard.intercept("Create a new task handler", clean_state)
        
        mock_gen.assert_called_once()
        assert state.status == AgentStatus.WAITING_FOR_HUMAN
        assert any("[GRILL-ME REPORT GENERATED]" in msg.content for msg in state.history)
        
        assert os.path.exists(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["objective"] == "Create a new task handler"
            assert "src/task.py" in data["files_affected"]
