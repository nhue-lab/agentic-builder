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

        action = decision.action.lower() if decision.action else ""
        is_skill_action = action in ("call_skill", "execute_script", "fetch_data", "run_skill", "execute_skill", "call_tool") or (decision.skill_name and action not in ("finish", "ask_human", "respond"))
        
        if is_skill_action:
            skill_name = decision.skill_name
            if not skill_name:
                raise ValueError("Action requests skill execution but 'skill_name' is missing.")

            # If LLM guessed a non-existent skill_name, give clear feedback listing registered skills
            if skill_name not in self.skills:
                available = ", ".join(self.skills.keys())
                return f"Skill '{skill_name}' is not registered. Available registered skills: [{available}]. Please use action: 'call_skill' with one of the available skills."

            # Rule: Pas de skill dans l'agent courant = PermissionError immédiat
            if skill_name not in state.injected_skills:
                raise PermissionError(f"Skill '{skill_name}' is not allowed for the current agent.")

            # Rule: Strict Read-Only lock until /grill-me is approved
            from config.settings import settings
            if settings.grill_me_enabled and not state.metadata.get("grill_me_approved") and state.status != AgentStatus.GRILL_ME_APPROVED:
                if skill_name not in settings.read_only_skills:
                    raise PermissionError(
                        f"Action '{skill_name}' rejected: system is locked in READ-ONLY mode until the /grill-me phase is approved by the user."
                    )

            skill = self.skills[skill_name]
            result = await skill.execute(decision.arguments, state)
            if result.success:
                return result.output
            else:
                raise RuntimeError(f"Skill '{skill_name}' failed: {result.error}")

        elif action in ("ask_human", "human_input"):
            state.status = AgentStatus.WAITING_FOR_HUMAN
            question = decision.arguments.get("question", "No question provided.")
            return f"Agent is waiting for human feedback. Question: {question}"

        elif action in ("respond", "answer"):
            state.status = AgentStatus.SUCCESS
            return decision.response or decision.thought or "Agent responded."

        elif action in ("finish", "done", "complete"):
            state.status = AgentStatus.SUCCESS
            return decision.response or decision.thought or "Task complete."

        else:
            raise ValueError(f"Unknown action type: {decision.action}. Allowed actions: 'call_skill', 'finish', 'ask_human', 'respond'.")
