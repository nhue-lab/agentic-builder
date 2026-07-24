import logging
import uuid
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.context.state import AgentState, AgentStatus
from config.settings import settings

logger = logging.getLogger("agentic_builder.skills.subagent")

class SubAgentSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "subagent"

    @property
    def description(self) -> str:
        return "Delegates a specific sub-task to a isolated sub-agent with restricted skills and context."

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        if not settings.subagent_enabled:
            return SkillResult(success=False, output="", error="Sub-agent execution is disabled in settings.")

        sub_task = arguments.get("sub_task")
        if not sub_task:
            return SkillResult(success=False, output="", error="Missing required argument 'sub_task'.")

        role = arguments.get("role", "researcher")

        # Depth check for recursion safety
        if state.depth >= settings.subagent_max_depth:
            logger.warning(f"Sub-agent depth limit reached (current depth: {state.depth}, max: {settings.subagent_max_depth}). Delegation rejected.")
            return SkillResult(
                success=False,
                output="",
                error=f"PermissionError: Sub-agent depth limit reached ({state.depth}/{settings.subagent_max_depth}). Sub-agents cannot spawn additional sub-agents."
            )

        logger.info(f"Spawning sub-agent for role '{role}' with task: '{sub_task}' (depth: {state.depth + 1})")

        # Restricted skills for sub-agent
        allowed_skills = [s for s in settings.subagent_allowed_skills if s != "subagent"]

        child_session_id = f"{state.session_id}_sub_{uuid.uuid4().hex[:6]}"
        child_state = AgentState(
            session_id=child_session_id,
            current_agent=role,
            injected_skills=allowed_skills,
            depth=state.depth + 1,
            max_iterations=10
        )

        from src.loop.engine import AgentEngine
        from src.loop.router import LoopRouter
        
        # Instantiate router with current skill dictionary
        # We reuse skills dict from caller or imported skills
        from src.harness.skills.researcher.skill import ResearcherSkill
        from src.harness.skills.tester.skill import TesterSkill
        
        registered_skills = {
            "researcher": ResearcherSkill(),
            "tester": TesterSkill()
        }
        child_router = LoopRouter(skills=registered_skills)
        child_engine = AgentEngine(child_router)

        try:
            result_state = await child_engine.run(sub_task, child_state)
            if result_state.status == AgentStatus.SUCCESS:
                output = result_state.metadata.get("proposed_response", "Sub-agent task complete.")
                return SkillResult(success=True, output=f"[Sub-Agent '{role}' Output]: {output}")
            else:
                errors = "; ".join(result_state.errors) or "Unknown failure"
                return SkillResult(success=False, output="", error=f"Sub-agent '{role}' failed: {errors}")
        except Exception as e:
            logger.error(f"Error running sub-agent: {e}")
            return SkillResult(success=False, output="", error=f"Sub-agent execution error: {str(e)}")
