import pytest
from src.context.state import LLMDecision, AgentStatus
from src.loop.router import LoopRouter

@pytest.mark.asyncio
async def test_loop_router_call_skill_success(mock_skill, clean_state):
    router = LoopRouter(skills={"mock_skill": mock_skill})
    decision = LLMDecision(
        thought="Use mock skill",
        action="call_skill",
        skill_name="mock_skill",
        arguments={"param": "value"}
    )
    
    result = await router.route(decision, clean_state)
    assert "Executed mock_skill" in result
    assert clean_state.status == AgentStatus.IDLE  # Status remains unchanged

@pytest.mark.asyncio
async def test_loop_router_call_skill_permission_denied(mock_skill, clean_state):
    router = LoopRouter(skills={"mock_skill": mock_skill, "forbidden_skill": mock_skill})
    decision = LLMDecision(
        thought="Use forbidden skill",
        action="call_skill",
        skill_name="forbidden_skill",
        arguments={}
    )
    
    # forbidden_skill is not in clean_state.injected_skills
    with pytest.raises(PermissionError) as exc_info:
        await router.route(decision, clean_state)
    assert "is not allowed for the current agent" in str(exc_info.value)

@pytest.mark.asyncio
async def test_loop_router_call_skill_not_registered(clean_state):
    # 'mock_skill' is in clean_state.injected_skills, but empty skills dict in router
    router = LoopRouter(skills={})
    decision = LLMDecision(
        thought="Use mock skill",
        action="call_skill",
        skill_name="mock_skill",
        arguments={}
    )
    
    with pytest.raises(ValueError) as exc_info:
        await router.route(decision, clean_state)
    assert "is injected in state but not registered in runner" in str(exc_info.value)

@pytest.mark.asyncio
async def test_loop_router_call_skill_missing_name(mock_skill, clean_state):
    router = LoopRouter(skills={"mock_skill": mock_skill})
    decision = LLMDecision(
        thought="Call skill but forget name",
        action="call_skill",
        skill_name=None,
        arguments={}
    )
    
    with pytest.raises(ValueError) as exc_info:
        await router.route(decision, clean_state)
    assert "skill_name' is missing" in str(exc_info.value)

@pytest.mark.asyncio
async def test_loop_router_call_skill_failure(mock_skill, clean_state):
    router = LoopRouter(skills={"mock_skill": mock_skill})
    decision = LLMDecision(
        thought="Run skill to trigger error",
        action="call_skill",
        skill_name="mock_skill",
        arguments={"fail": True}
    )
    
    with pytest.raises(RuntimeError) as exc_info:
        await router.route(decision, clean_state)
    assert "Mock skill forced failure" in str(exc_info.value)

@pytest.mark.asyncio
async def test_loop_router_ask_human(clean_state):
    router = LoopRouter(skills={})
    decision = LLMDecision(
        thought="Need human clarification",
        action="ask_human",
        arguments={"question": "Is this OK?"}
    )
    
    result = await router.route(decision, clean_state)
    assert clean_state.status == AgentStatus.WAITING_FOR_HUMAN
    assert "Question: Is this OK?" in result

@pytest.mark.asyncio
async def test_loop_router_respond(clean_state):
    router = LoopRouter(skills={})
    decision = LLMDecision(
        thought="Formulate response",
        action="respond",
        response="Here is your answer."
    )
    
    result = await router.route(decision, clean_state)
    assert clean_state.status == AgentStatus.SUCCESS
    assert result == "Here is your answer."

@pytest.mark.asyncio
async def test_loop_router_finish(clean_state):
    router = LoopRouter(skills={})
    decision = LLMDecision(
        thought="Task is done",
        action="finish",
        response="Completed successfully."
    )
    
    result = await router.route(decision, clean_state)
    assert clean_state.status == AgentStatus.SUCCESS
    assert result == "Completed successfully."

@pytest.mark.asyncio
async def test_loop_router_unknown_action(clean_state):
    router = LoopRouter(skills={})
    decision = LLMDecision(
        thought="Perform invalid action",
        action="invalid_action"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await router.route(decision, clean_state)
    assert "Unknown action type" in str(exc_info.value)
