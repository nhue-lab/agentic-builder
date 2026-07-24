import logging
from typing import Any
from src.context.state import LLMDecision, AgentState, AgentStatus
from src.harness.skills.base_skill import BaseSkill

logger = logging.getLogger("agentic_builder.loop.router")

class LoopRouter:
    def __init__(self, skills: dict[str, BaseSkill]):
        self.skills = skills

    async def route(self, decision: LLMDecision, state: AgentState) -> str:
        logger.info(f"Routing action: {decision.action} (skill: {decision.skill_name})")
        
        if decision.action == "call_skill":
            skill_name = decision.skill_name
            if not skill_name:
                raise ValueError("Action is 'call_skill' but 'skill_name' is missing.")

            # Rule: Pas de skill dans l'agent courant = PermissionError immédiat
            if skill_name not in state.injected_skills:
                raise PermissionError(f"Skill '{skill_name}' is not allowed for the current agent.")

            # Rule: Strict Read-Only lock until /grill-me is approved
            from config.settings import settings
            if settings.grill_me_enabled and state.status != AgentStatus.GRILL_ME_APPROVED:
                if skill_name not in settings.read_only_skills:
                    raise PermissionError(
                        f"Action '{skill_name}' rejected: system is locked in READ-ONLY mode until the /grill-me phase is approved by the user."
                    )

            skill = self.skills.get(skill_name)
            if not skill:
                raise ValueError(f"Skill '{skill_name}' is injected in state but not registered in runner.")

            result = await skill.execute(decision.arguments, state)
            if result.success:
                return result.output
            else:
                raise RuntimeError(f"Skill '{skill_name}' failed: {result.error}")

        elif decision.action == "ask_human":
            state.status = AgentStatus.WAITING_FOR_HUMAN
            question = decision.arguments.get("question", "No question provided.")
            return f"Agent is waiting for human feedback. Question: {question}"

        elif decision.action == "respond":
            state.status = AgentStatus.SUCCESS
            return decision.response or "Agent responded."

        elif decision.action == "finish":
            state.status = AgentStatus.SUCCESS
            return decision.response or "Task complete."

        else:
            raise ValueError(f"Unknown action type: {decision.action}")
