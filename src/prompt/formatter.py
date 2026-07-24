import os
from jinja2 import Template

class PromptFormatter:
    @staticmethod
    def render_template(template_path: str, context: dict) -> str:
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        template = Template(template_content)
        return template.render(**context)

    @staticmethod
    def count_tokens_approx(text: str) -> int:
        # Simple approximation of 4 characters per token
        return len(text) // 4
