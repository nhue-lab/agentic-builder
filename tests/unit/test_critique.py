import pytest
from src.loop.critique import CritiqueAgent, CritiqueResult
from src.context.state import AgentState

@pytest.mark.asyncio
async def test_critique_agent_evaluation():
    state = AgentState(session_id="test-session")
    critique = await CritiqueAgent.evaluate(
        task="Write a hello world program",
        result="print('Hello, World!')",
        state=state
    )
    assert isinstance(critique, CritiqueResult)
    assert critique.score >= 0.0 and critique.score <= 1.0
    assert isinstance(critique.is_acceptable, bool)

