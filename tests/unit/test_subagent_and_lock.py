import pytest
from src.context.state import AgentState, AgentStatus, LLMDecision
from src.loop.router import LoopRouter
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.harness.skills.subagent.subagent_skill import SubAgentSkill
from src.harness.skills.researcher.skill import ResearcherSkill
from config.settings import settings

class MockWriteSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "git_push"

    @property
    def description(self) -> str:
        return "Mock write skill"

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        return SkillResult(success=True, output="Pushed")

@pytest.mark.asyncio
async def test_read_only_lock_rejects_write_skills():
    settings.grill_me_enabled = True
    state = AgentState(
        session_id="test_read_only",
        status=AgentStatus.RUNNING,  # NOT GRILL_ME_APPROVED
        injected_skills=["researcher", "git_push"]
    )
    router = LoopRouter(skills={
        "researcher": ResearcherSkill(),
        "git_push": MockWriteSkill()
    })

    # Allowed read-only skill
    read_decision = LLMDecision(
        thought="Lire documentation",
        action="call_skill",
        skill_name="researcher",
        arguments={"query": "test"}
    )
    res = await router.route(read_decision, state)
    assert res is not None

    # Forbidden write skill during Grill-Me pending phase
    write_decision = LLMDecision(
        thought="Push code",
        action="call_skill",
        skill_name="git_push",
        arguments={"message": "fix"}
    )
    with pytest.raises(PermissionError, match="locked in READ-ONLY mode"):
        await router.route(write_decision, state)

@pytest.mark.asyncio
async def test_subagent_depth_limit():
    subagent_skill = SubAgentSkill()
    state = AgentState(
        session_id="test_sub_depth",
        depth=1,  # Already at max depth (max_depth=1)
        injected_skills=["subagent"]
    )
    result = await subagent_skill.execute({"sub_task": "test"}, state)
    assert result.success is False
    assert "Sub-agent depth limit reached" in result.error
