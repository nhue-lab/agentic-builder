import pytest
from unittest.mock import AsyncMock, patch
from src.context.state import AgentState, AgentStatus
from src.loop.task_loop import TaskLoop
from src.loop.critique import CritiqueResult

@pytest.mark.asyncio
async def test_task_loop_success_on_first_try(clean_state):
    # Setup
    mock_engine = AsyncMock()
    
    async def mock_run(task, state):
        state.status = AgentStatus.SUCCESS
        state.metadata["proposed_response"] = "Correct output"
        return state
        
    mock_engine.run.side_effect = mock_run
    
    task_loop = TaskLoop(engine=mock_engine)
    clean_state.max_task_attempts = 3
    
    # Mock CritiqueAgent to approve the first try
    with patch("src.loop.critique.CritiqueAgent.evaluate", new_callable=AsyncMock) as mock_critique:
        mock_critique.return_value = CritiqueResult(score=1.0, is_acceptable=True, feedback="")
        
        final_state = await task_loop.run("Task description", clean_state)
        
        # Verify
        assert final_state.status == AgentStatus.SUCCESS
        assert final_state.task_attempt == 1
        assert len(final_state.post_mortems) == 0
        assert mock_engine.run.call_count == 1

@pytest.mark.asyncio
async def test_task_loop_success_on_second_try(clean_state):
    # Setup
    mock_engine = AsyncMock()
    
    async def mock_run(task, state):
        state.status = AgentStatus.SUCCESS
        state.metadata["proposed_response"] = f"Output for attempt {state.task_attempt}"
        return state
        
    mock_engine.run.side_effect = mock_run
    
    task_loop = TaskLoop(engine=mock_engine)
    clean_state.max_task_attempts = 3
    
    # Mock CritiqueAgent to reject the first try and accept the second try
    with patch("src.loop.critique.CritiqueAgent.evaluate", new_callable=AsyncMock) as mock_critique:
        mock_critique.side_effect = [
            CritiqueResult(score=0.2, is_acceptable=False, feedback="Incorrect calculation"),
            CritiqueResult(score=1.0, is_acceptable=True, feedback="")
        ]
        
        final_state = await task_loop.run("Task description", clean_state)
        
        # Verify
        assert final_state.status == AgentStatus.SUCCESS
        assert final_state.task_attempt == 2
        assert len(final_state.post_mortems) == 1
        assert final_state.post_mortems[0] == "Incorrect calculation"
        assert mock_engine.run.call_count == 2
        
        # Verify history reset and post-mortem injection on second attempt state
        # The history should contain the warning alert system message
        assert any("Incorrect calculation" in msg.content for msg in final_state.history if msg.role == "system")

@pytest.mark.asyncio
async def test_task_loop_failure_after_max_attempts(clean_state):
    # Setup
    mock_engine = AsyncMock()
    
    async def mock_run(task, state):
        state.status = AgentStatus.SUCCESS
        state.metadata["proposed_response"] = f"Failed output {state.task_attempt}"
        return state
        
    mock_engine.run.side_effect = mock_run
    
    task_loop = TaskLoop(engine=mock_engine)
    clean_state.max_task_attempts = 2
    
    # Mock CritiqueAgent to reject all tries
    with patch("src.loop.critique.CritiqueAgent.evaluate", new_callable=AsyncMock) as mock_critique:
        mock_critique.return_value = CritiqueResult(score=0.1, is_acceptable=False, feedback="Always wrong")
        
        final_state = await task_loop.run("Task description", clean_state)
        
        # Verify
        assert final_state.status == AgentStatus.FAILED
        assert final_state.task_attempt == 2
        assert len(final_state.post_mortems) == 2
        assert mock_engine.run.call_count == 2
        assert "Validation failed after maximum task attempts." in final_state.errors
