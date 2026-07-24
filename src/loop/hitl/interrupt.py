import os
import logging
from src.context.state import AgentState, AgentStatus

logger = logging.getLogger("agentic_builder.loop.hitl.interrupt")

class LoopInterrupt:
    @staticmethod
    def interrupt_for_human(state: AgentState, question: str) -> str:
        logger.info(f"Interrupting job {state.session_id} for human validation.")
        state.status = AgentStatus.WAITING_FOR_HUMAN
        
        # Serialize state
        os.makedirs(".agent", exist_ok=True)
        with open(".agent/state.json", "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
            
        print(f"\n==================================================")
        print(f"[WARNING] HUMAN INPUT REQUIRED (Session: {state.session_id})")
        print(f"Question: {question}")
        print(f"==================================================\n")
        
        return f"Interrupted. Awaiting response to: {question}"
