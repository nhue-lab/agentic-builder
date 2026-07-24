import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentic_builder.telemetry.trajectory")

class TrajectoryStep(BaseModel):
    iteration: int
    thought: str
    action: str
    skill_name: Optional[str] = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    observation: str
    success: bool
    timestamp: str

class TrajectoryLogger:
    @staticmethod
    def export(session_id: str, task: str, steps: list[TrajectoryStep], final_status: str) -> str:
        os_dir = ".agent"
        os.makedirs(os_dir, exist_ok=True)
        file_path = os.path.join(os_dir, f"trajectory_{session_id}.jsonl")

        header = {
            "session_id": session_id,
            "task": task,
            "final_status": final_status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_steps": len(steps)
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"metadata": header}) + "\n")
                for step in steps:
                    f.write(json.dumps({"step": step.model_dump()}) + "\n")
            logger.info(f"Exported trajectory to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to export trajectory for session {session_id}: {e}")
            return ""
