import re
import json
import logging
from src.context.state import LLMDecision

logger = logging.getLogger("agentic_builder.guardrails.output_filter")

class OutputParseError(ValueError):
    """Exception raised when output parsing or validation fails."""
    pass

class OutputFilter:
    @classmethod
    def extract_json(cls, raw_content: str) -> dict:
        # Match ```json ... ```, ``` ... ```, or plain JSON
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, raw_content, re.DOTALL)
        
        json_str = raw_content
        if match:
            json_str = match.group(1)
        else:
            # Try to search for the first '{' and last '}'
            start_idx = raw_content.find('{')
            end_idx = raw_content.rfind('}')
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = raw_content[start_idx:end_idx + 1]

        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from content. Error: {str(e)}")
            raise OutputParseError(
                f"Output is not a valid JSON structure. Ensure your response contains a JSON block. "
                f"Error detail: {str(e)}"
            )

    @classmethod
    def validate_decision(cls, raw_content: str) -> LLMDecision:
        parsed_data = cls.extract_json(raw_content)
        try:
            return LLMDecision.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"JSON parsed but Pydantic validation failed: {str(e)}")
            raise OutputParseError(
                f"JSON object does not match the LLMDecision schema. "
                f"Validation error: {str(e)}"
            )
