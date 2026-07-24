import pytest
from src.harness.skills.tester.skill import TesterSkill

@pytest.mark.asyncio
async def test_tester_skill_execution(clean_state):
    skill = TesterSkill()
    assert skill.name == "tester"
    
    # Execution on a valid test file should succeed
    result = await skill.execute({"test_path": "tests/unit/test_state.py"}, clean_state)
    assert result.success is True
    assert "passed" in result.output.lower() or "collected" in result.output.lower()

    # Execution on a non-existent path should fail
    fail_result = await skill.execute({"test_path": "tests/unit/non_existent_file.py"}, clean_state)
    assert fail_result.success is False
    assert fail_result.error is not None
