from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from typing import Any, Optional

class LLMResponse(BaseModel):
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(
        self, 
        messages: list[dict[str, str]], 
        response_schema: Optional[Any] = None, 
        **kwargs
    ) -> LLMResponse:
        pass

