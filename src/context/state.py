from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    GRILL_ME_APPROVED = "GRILL_ME_APPROVED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

from pydantic import BaseModel, Field, model_validator

class Message(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    timestamp: str
    priority: int = 0
    token_count: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def set_priority_and_tokens(cls, data: Any) -> Any:
        if isinstance(data, dict):
            role = data.get("role", "user")
            if "priority" not in data or data.get("priority") is None:
                if role == "system":
                    data["priority"] = 2
                elif role in ("tool", "user") and "Observation:" in data.get("content", ""):
                    data["priority"] = 1
                else:
                    data["priority"] = 0
            if "token_count" not in data or data.get("token_count") is None:
                content = data.get("content", "")
                data["token_count"] = (len(content) // 4) + 10
        return data

class LLMDecision(BaseModel):
    thought: str
    action: str          # "call_skill" | "respond" | "finish" | "ask_human"
    skill_name: Optional[str] = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    response: Optional[str] = None

class AgentState(BaseModel):
    session_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_agent: str = "orchestrator"
    history: list[Message] = Field(default_factory=list)
    injected_skills: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    critique_scores: list[float] = Field(default_factory=list)
    consecutive_errors: int = 0
    iteration: int = 0
    max_iterations: int = 15
    task_attempt: int = 1
    max_task_attempts: int = 3
    post_mortems: list[str] = Field(default_factory=list)
    depth: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load_from_file(cls, path: str) -> "AgentState":
        import os
        import json
        if not os.path.exists(path):
            raise FileNotFoundError(f"State file not found at: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content in state file: {e}") from e
        
        try:
            state = cls.model_validate(data)
        except Exception as e:
            raise ValueError(f"Invalid state structure: {e}") from e
        
        state.status = AgentStatus.RUNNING
        state.consecutive_errors = 0
        return state

