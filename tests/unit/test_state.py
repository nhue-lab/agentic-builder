import pytest
import json
from src.context.state import AgentState, AgentStatus, Message, LLMDecision

def test_agent_status_values():
    assert AgentStatus.IDLE == "IDLE"
    assert AgentStatus.RUNNING == "RUNNING"
    assert AgentStatus.WAITING_FOR_HUMAN == "WAITING_FOR_HUMAN"
    assert AgentStatus.SUCCESS == "SUCCESS"
    assert AgentStatus.FAILED == "FAILED"

def test_message_auto_priority():
    # 1. System messages should automatically have priority 2
    msg_sys = Message(role="system", content="System Prompt", timestamp="2026-07-06")
    assert msg_sys.priority == 2
    
    # 2. Observation messages (user/tool role containing "Observation:") should have priority 1
    msg_obs_user = Message(role="user", content="Observation: success", timestamp="2026-07-06")
    assert msg_obs_user.priority == 1
    
    msg_obs_tool = Message(role="tool", content="Observation: error", timestamp="2026-07-06")
    assert msg_obs_tool.priority == 1
    
    # 3. Normal user/assistant/tool messages should have priority 0
    msg_user = Message(role="user", content="Hello, agent", timestamp="2026-07-06")
    assert msg_user.priority == 0
    
    msg_assistant = Message(role="assistant", content="How can I help?", timestamp="2026-07-06")
    assert msg_assistant.priority == 0
    
    # 4. Explicit priority should override defaults
    msg_explicit = Message(role="system", content="System Prompt", timestamp="2026-07-06", priority=0)
    assert msg_explicit.priority == 0

def test_message_token_estimation():
    # Test fallback estimation: (len(content) // 4) + 10
    content = "Hello world of AI"  # len = 17. 17 // 4 + 10 = 14
    msg = Message(role="user", content=content, timestamp="2026-07-06")
    assert msg.token_count == 14
    
    # Test explicit token_count override
    msg_explicit = Message(role="user", content=content, timestamp="2026-07-06", token_count=50)
    assert msg_explicit.token_count == 50

def test_llm_decision_validation():
    # Valid call_skill decision
    decision_dict = {
        "thought": "I should call the mock skill",
        "action": "call_skill",
        "skill_name": "mock_skill",
        "arguments": {"key": "val"}
    }
    decision = LLMDecision.model_validate(decision_dict)
    assert decision.thought == "I should call the mock skill"
    assert decision.action == "call_skill"
    assert decision.skill_name == "mock_skill"
    assert decision.arguments == {"key": "val"}
    assert decision.response is None
    
    # Missing required field 'action'
    with pytest.raises(ValueError):
        LLMDecision.model_validate({"thought": "thinking"})

def test_agent_state_defaults():
    state = AgentState(session_id="session-123")
    assert state.session_id == "session-123"
    assert state.status == AgentStatus.IDLE
    assert state.current_agent == "orchestrator"
    assert state.history == []
    assert state.injected_skills == []
    assert state.errors == []
    assert state.consecutive_errors == 0
    assert state.iteration == 0
    assert state.max_iterations == 15
    assert state.task_attempt == 1
    assert state.max_task_attempts == 3

def test_agent_state_serialization():
    state = AgentState(
        session_id="test-session",
        status=AgentStatus.RUNNING,
        history=[
            Message(role="system", content="System Prompt", timestamp="2026-07-06"),
            Message(role="user", content="Hello", timestamp="2026-07-06")
        ]
    )
    
    serialized = state.model_dump_json()
    deserialized = AgentState.model_validate_json(serialized)
    
    assert deserialized.session_id == state.session_id
    assert deserialized.status == AgentStatus.RUNNING
    assert len(deserialized.history) == 2
    assert deserialized.history[0].role == "system"
    assert deserialized.history[0].priority == 2
    assert deserialized.history[1].role == "user"
    assert deserialized.history[1].priority == 0

def test_agent_state_load_from_file_success(tmp_path):
    state_file = tmp_path / "state.json"
    state = AgentState(
        session_id="test-session-load",
        status=AgentStatus.SUCCESS,
        consecutive_errors=3
    )
    state_file.write_text(state.model_dump_json(), encoding="utf-8")
    
    loaded_state = AgentState.load_from_file(str(state_file))
    
    assert loaded_state.session_id == "test-session-load"
    assert loaded_state.status == AgentStatus.RUNNING  # Forced to RUNNING
    assert loaded_state.consecutive_errors == 0       # Forced to 0

def test_agent_state_load_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        AgentState.load_from_file("non_existent_file_path.json")

def test_agent_state_load_from_file_invalid_json(tmp_path):
    state_file = tmp_path / "invalid_state.json"
    state_file.write_text("invalid json content", encoding="utf-8")
    
    with pytest.raises(ValueError, match="Invalid JSON content"):
        AgentState.load_from_file(str(state_file))

def test_agent_state_load_from_file_invalid_structure(tmp_path):
    state_file = tmp_path / "invalid_struct.json"
    state_file.write_text('{"unknown_field": 123}', encoding="utf-8")
    
    with pytest.raises(ValueError, match="Invalid state structure"):
        AgentState.load_from_file(str(state_file))

