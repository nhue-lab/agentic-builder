from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional
from src.context.state import AgentState

class SkillResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None

class BaseSkill(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        pass
