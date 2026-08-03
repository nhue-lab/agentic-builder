from typing import Any, Optional
import os
import json
from src.lms.base_client import BaseLLMClient, LLMResponse

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str = "", model_name: str = "gemini-2.5-pro"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("[GeminiClient] google-genai SDK not installed. Running in mock/simulation mode.")

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
                if "action" in response_schema.model_fields:
                    mock_dict["action"] = "call_skill"
                    mock_dict["thought"] = "Executing skill in simulation mode."
                    mock_dict["skill_name"] = "researcher"
                    mock_dict["arguments"] = {"query": "LLM benchmark cost per task data"}
                for k, field in response_schema.model_fields.items():
                    if k not in mock_dict:
                        # Inspect annotation safely
                        annotation_str = str(field.annotation)
                        if "dict" in annotation_str.lower():
                            mock_dict[k] = {}
                        elif "list" in annotation_str.lower():
                            mock_dict[k] = ["mock_value"]
                        elif "str" in annotation_str.lower():
                            mock_dict[k] = "mock_value"
                        elif "bool" in annotation_str.lower():
                            mock_dict[k] = True
                        elif "int" in annotation_str.lower() or "float" in annotation_str.lower():
                            mock_dict[k] = 1
                        else:
                            mock_dict[k] = {}
                mock_content = json.dumps(mock_dict)
            else:
                # Simulation/Mock Response
                mock_content = json.dumps({
                    "thought": "I need to look for recent trends using the web research tool.",
                    "action": "call_skill",
                    "skill_name": "researcher",
                    "arguments": {"query": "recent AI trends 2026"}
                })
                # If the last message contains "simulation finish", finish the task, or if we already ran a skill
                last_message_content = messages[-1]["content"] if messages else ""
                if "finish" in last_message_content.lower() or "completed" in last_message_content.lower() or any("Observation" in m["content"] for m in messages):
                    mock_content = json.dumps({
                        "thought": "The task is successfully completed.",
                        "action": "finish",
                        "response": "Simulation finished successfully."
                    })
            
            return LLMResponse(
                content=mock_content,
                input_tokens=100,
                output_tokens=50,
                model=f"{self.model_name}-mock"
            )
        
        # Real SDK Call
        from google.genai import types
        # Map roles and build contents
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role_map = {"user": "user", "assistant": "model"}
                contents.append(
                    types.Content(
                        role=role_map.get(msg["role"], "user"),
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
        
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", 0.2),
            system_instruction=system_instruction
        )
        if response_schema:
            config.response_mime_type = "application/json"
            if hasattr(response_schema, "model_json_schema"):
                raw_schema = response_schema.model_json_schema()
                def _strip_additional_properties(d):
                    if isinstance(d, dict):
                        return {k: _strip_additional_properties(v) for k, v in d.items() if k != "additionalProperties"}
                    elif isinstance(d, list):
                        return [_strip_additional_properties(x) for x in d]
                    return d
                config.response_schema = _strip_additional_properties(raw_schema)
            else:
                config.response_schema = response_schema

        target_model = kwargs.get("model", self.model_name)
        response = await self.client.aio.models.generate_content(
            model=target_model,
            contents=contents,
            config=config
        )
        
        input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
        
        return LLMResponse(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_name
        )
