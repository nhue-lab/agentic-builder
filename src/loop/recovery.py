import logging
from datetime import datetime, timezone
from src.context.state import AgentState, AgentStatus, Message

logger = logging.getLogger("agentic_builder.loop.recovery")

class LoopRecovery:
    @staticmethod
    async def recover(exc: Exception, state: AgentState):
        error_msg = f"Error: {type(exc).__name__}: {str(exc)}"
        logger.warning(f"Error caught in loop iteration: {error_msg}")
        
        state.errors.append(error_msg)
        state.consecutive_errors += 1
        
        # Granular self-correction prompt based on error type
        from src.harness.guardrails.output_filter import OutputParseError
        
        if isinstance(exc, OutputParseError):
            correction_message = (
                f"Your output could not be parsed or validated against the schema:\n{str(exc)}\n"
                "Please output a valid JSON object matching the JSON Schema. "
                "Ensure you do not include raw explanations outside the JSON block."
            )
        else:
            correction_message = (
                f"An error occurred while executing the action:\n{error_msg}\n"
                "Please analyze the error, correct your parameters or choice, and try again."
            )
        
        state.history.append(Message(
            role="user",
            content=f"Observation: {correction_message}",
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
        
        # If we have too many errors in a row, fail the task
        if state.consecutive_errors >= 3:
            logger.error("Too many consecutive errors. Aborting task execution.")
            state.status = AgentStatus.FAILED

