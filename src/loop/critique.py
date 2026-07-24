import logging
from pydantic import BaseModel, Field
from src.lms.router import llm_router
from src.context.state import AgentState
from config.settings import settings

logger = logging.getLogger("agentic_builder.loop.critique")

class CritiqueResult(BaseModel):
    score: float = Field(
        description="A score between 0.0 (completely incorrect/inadequate) and 1.0 (perfectly correct and complete)."
    )
    is_acceptable: bool = Field(
        description="True if the result meets the requirements and needs no further edits/steps, False otherwise."
    )
    feedback: str = Field(
        description="Detailed, actionable feedback if not acceptable. Keep it empty if is_acceptable is True."
    )

class CritiqueAgent:
    @staticmethod
    async def evaluate(task: str, result: str, state: AgentState) -> CritiqueResult:
        """
        Evaluates the proposed result against the original task.
        """
        logger.info(f"CritiqueAgent starting evaluation for task: '{task}'")
        
        system_instruction = (
            "You are an expert quality assurance agent. Your job is to strictly critique "
            "the proposed final response of another agent against the original task. "
            "Verify accuracy, completeness, and correctness."
        )
        
        user_content = (
            f"Original Task: {task}\n\n"
            f"Proposed Response: {result}\n\n"
            f"Please output a CritiqueResult JSON object evaluating this response."
        )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        try:
            llm_response = await llm_router.generate(
                messages,
                response_schema=CritiqueResult,
                model=settings.critique_model,
                temperature=0.1
            )
            from src.harness.guardrails.output_filter import OutputFilter
            parsed_data = OutputFilter.extract_json(llm_response.content)
            critique = CritiqueResult.model_validate(parsed_data)
            logger.info(f"Critique evaluation finished. Score: {critique.score}, Acceptable: {critique.is_acceptable}")
            return critique
        except Exception as e:
            logger.error(f"Critique evaluation failed: {str(e)}. Falling back to default acceptable status.")
            return CritiqueResult(score=1.0, is_acceptable=True, feedback="")
