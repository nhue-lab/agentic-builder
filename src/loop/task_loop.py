import logging
from datetime import datetime, timezone
from src.context.state import AgentState, AgentStatus, Message, LLMDecision
from src.loop.engine import AgentEngine
from src.loop.critique import CritiqueAgent
from src.prompt.schema_injector import SchemaInjector
from src.prompt.formatter import PromptFormatter
from config.settings import settings

logger = logging.getLogger("agentic_builder.loop.task_loop")

class TaskLoop:
    def __init__(self, engine: AgentEngine):
        self.engine = engine

    async def run(self, task: str, state: AgentState) -> AgentState:
        logger.info(f"Starting TaskLoop for task: '{task}' (Attempt {state.task_attempt}/{state.max_task_attempts})")
        
        while state.task_attempt <= state.max_task_attempts:
            # 1. Run the inner ReAct execution loop
            state = await self.engine.run(task, state)
            
            # If the engine finished with failure or is waiting for human input, we exit the loop immediately.
            if state.status != AgentStatus.SUCCESS:
                logger.info(f"TaskLoop exiting early with status: {state.status}")
                return state

            # 2. Extract proposed response
            proposed_response = state.metadata.get("proposed_response", "No proposed response.")
            logger.info("Proposed response received. Invoking CritiqueAgent evaluation...")

            # 3. Evaluate the proposed response
            critique = await CritiqueAgent.evaluate(task, proposed_response, state)
            state.critique_scores.append(critique.score)

            if critique.is_acceptable:
                logger.info("Critique accepted the response. Task complete!")
                return state
            
            # Critique rejected the response
            logger.warning(f"Critique rejected the response. Feedback: {critique.feedback}")
            state.post_mortems.append(critique.feedback)

            if state.task_attempt >= state.max_task_attempts:
                logger.error("Max task attempts reached. Terminating task loop.")
                state.status = AgentStatus.FAILED
                state.errors.append("Validation failed after maximum task attempts.")
                return state

            # 4. Initialize a clean state for the next attempt (Ralph Loop / Fresh Context)
            logger.info(f"Preparing fresh context for Attempt {state.task_attempt + 1}")
            
            # Create a brand new state, keeping metadata, critique history, and incrementing attempts
            next_state = AgentState(
                session_id=state.session_id,
                injected_skills=state.injected_skills,
                task_attempt=state.task_attempt + 1,
                max_task_attempts=state.max_task_attempts,
                post_mortems=state.post_mortems,
                critique_scores=state.critique_scores,
                metadata=state.metadata
            )
            
            # Pre-initialize the history of next_state to include the post-mortem
            decision_schema = SchemaInjector.get_json_schema(LLMDecision)
            system_prompt = PromptFormatter.render_template(
                settings.system_prompt_path,
                {
                    "available_skills": ", ".join(next_state.injected_skills),
                    "response_schema": decision_schema
                }
            )
            
            # System instructions
            next_state.history.append(Message(
                role="system", 
                content=system_prompt, 
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            
            # Post-mortem warning
            post_mortem_summary = "\n".join([f"- Attempt {i+1}: {feedback}" for i, feedback in enumerate(next_state.post_mortems)])
            alert_message = (
                f"WARNING: Your previous attempt(s) to solve this task failed validation. "
                f"Please analyze the feedback from the QA reviewer below, correct your approach, and try again.\n"
                f"Validation Failures:\n{post_mortem_summary}"
            )
            next_state.history.append(Message(
                role="system", 
                content=alert_message, 
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            
            # Original task
            next_state.history.append(Message(
                role="user", 
                content=task, 
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

            state = next_state

        return state
