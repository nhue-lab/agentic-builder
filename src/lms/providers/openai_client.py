from typing import Any, Optional
import os
import json
from src.lms.base_client import BaseLLMClient, LLMResponse

class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str = "", model_name: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                print("[OpenAIClient] openai SDK not installed. Running in mock/simulation mode.")

    async def generate(
        self, 
        messages: list[dict[str, str]], 
        response_schema: Optional[Any] = None, 
        **kwargs
    ) -> LLMResponse:
        if not self.client:
            if response_schema and hasattr(response_schema, "model_fields"):
                mock_dict = {}
                if "score" in response_schema.model_fields:
                    mock_dict["score"] = 0.9
                if "is_acceptable" in response_schema.model_fields:
                    mock_dict["is_acceptable"] = True
                if "feedback" in response_schema.model_fields:
                    mock_dict["feedback"] = "Excellent results."
                for k, field in response_schema.model_fields.items():
                    if k not in mock_dict:
                        # Inspect annotation safely
                        annotation_str = str(field.annotation)
                        if "str" in annotation_str:
                            mock_dict[k] = "mock_value"
                        elif "bool" in annotation_str:
                            mock_dict[k] = True
                        elif "int" in annotation_str or "float" in annotation_str:
                            mock_dict[k] = 1
                        else:
                            mock_dict[k] = {}
                mock_content = json.dumps(mock_dict)
            else:
                # Mock Response
                mock_content = json.dumps({
                    "thought": "Using fallback mock OpenAI client to finish task.",
                    "action": "finish",
                    "response": "Fallback execution completed."
                })
            return LLMResponse(
                content=mock_content,
                input_tokens=50,
                output_tokens=25,
                model=f"{self.model_name}-mock"
            )

        # Real Call
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        target_model = kwargs.get("model", self.model_name)
        kwargs_call = {
            "model": target_model,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", 0.2)
        }

        if response_schema:
            try:
                response = await self.client.beta.chat.completions.parse(
                    **kwargs_call,
                    response_format=response_schema
                )
            except Exception as e:
                kwargs_call["response_format"] = {"type": "json_object"}
                response = await self.client.chat.completions.create(**kwargs_call)
        else:
            response = await self.client.chat.completions.create(**kwargs_call)

        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        return LLMResponse(
            content=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_name
        )

