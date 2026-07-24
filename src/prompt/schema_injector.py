import json
from typing import Type
from pydantic import BaseModel

class SchemaInjector:
    @staticmethod
    def get_json_schema(model_class: Type[BaseModel]) -> str:
        """
        Generates a clean JSON string representation of a Pydantic model's JSON Schema.
        """
        schema = model_class.model_json_schema()
        return json.dumps(schema, indent=2)
