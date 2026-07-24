import pytest
from src.loop.recovery import LoopRecovery
from src.context.state import AgentState, AgentStatus
from src.harness.guardrails.output_filter import OutputParseError

@pytest.mark.asyncio
async def test_loop_recovery_output_parse_error():
    state = AgentState(session_id="test-session")
    exc = OutputParseError("Invalid format details")
    
    await LoopRecovery.recover(exc, state)
    
    assert state.consecutive_errors == 1
    assert len(state.errors) == 1
    assert "Error: OutputParseError: Invalid format details" in state.errors[0]
    
    # Verify specific JSON correction instruction in history
    last_msg = state.history[-1]
    assert last_msg.role == "user"
    assert "Observation: Your output could not be parsed" in last_msg.content
    assert "output a valid JSON object matching the JSON Schema" in last_msg.content

@pytest.mark.asyncio
async def test_loop_recovery_generic_error():
    state = AgentState(session_id="test-session")
    exc = ValueError("Some internal database crash")
    
    await LoopRecovery.recover(exc, state)
    
    assert state.consecutive_errors == 1
    assert len(state.errors) == 1
    assert "Error: ValueError: Some internal database crash" in state.errors[0]
    
    # Verify generic self-healing instructions in history
    last_msg = state.history[-1]
    assert last_msg.role == "user"
    assert "Observation: An error occurred while executing the action" in last_msg.content
    assert "analyze the error, correct your parameters" in last_msg.content

@pytest.mark.asyncio
async def test_loop_recovery_circuit_breaker_trigger():
    state = AgentState(session_id="test-session", status=AgentStatus.RUNNING)
    exc = RuntimeError("Generic operation failure")
    
    # 1st error
    await LoopRecovery.recover(exc, state)
    assert state.consecutive_errors == 1
    assert state.status == AgentStatus.RUNNING
    
    # 2nd error
    await LoopRecovery.recover(exc, state)
    assert state.consecutive_errors == 2
    assert state.status == AgentStatus.RUNNING
    
    # 3rd error -> triggers circuit breaker failure state
    await LoopRecovery.recover(exc, state)
    assert state.consecutive_errors == 3
    assert state.status == AgentStatus.FAILED
