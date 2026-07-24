import pytest
import json
from src.context.state import AgentState, AgentStatus
from src.harness.skills.researcher.skill import ResearcherSkill
from src.loop.router import LoopRouter
from src.loop.engine import AgentEngine
from src.lms.router import llm_router
from tests.conftest import MockLLMClient

@pytest.mark.asyncio
async def test_engine_loop_success_workflow(clean_state):
    # Setup mock LLM response that calls researcher first, then finishes
    mock_responses = [
        # Step 1
        json.dumps({
            "thought": "I will search for the query",
            "action": "call_skill",
            "skill_name": "researcher",
            "arguments": {"query": "test query"}
        }),
        # Step 2
        json.dumps({
            "thought": "Finished the task.",
            "action": "finish",
            "response": "Search completed successfully."
        })
    ]
    
    # We monkeypatch the generate call of the llm_router
    call_idx = 0
    async def mock_generate(messages, **kwargs):
        nonlocal call_idx
        res = mock_responses[call_idx]
        call_idx += 1
        from src.lms.base_client import LLMResponse
        return LLMResponse(content=res, input_tokens=10, output_tokens=5, model="mock")
        
    llm_router.generate = mock_generate

    skills_map = {"researcher": ResearcherSkill()}
    router = LoopRouter(skills=skills_map)
    engine = AgentEngine(router=router)
    
    clean_state.injected_skills = ["researcher"]
    
    final_state = await engine.run("Find information", clean_state)
    
    assert final_state.status == AgentStatus.SUCCESS
    assert final_state.iteration == 2
    assert len(final_state.errors) == 0
