import pytest
from src.harness.skills.researcher.skill import ResearcherSkill

@pytest.mark.asyncio
async def test_researcher_skill_execution(clean_state):
    skill = ResearcherSkill()
    assert skill.name == "researcher"
    
    result = await skill.execute({"query": "agents"}, clean_state)
    assert result.success is True
    assert "Search results" in result.output

    fail_result = await skill.execute({}, clean_state)
    assert fail_result.success is False
    assert fail_result.error == "Missing 'query' argument."
