import pytest
from src.context.state import AgentState, AgentStatus
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.lms.base_client import BaseLLMClient, LLMResponse

class MockLLMClient(BaseLLMClient):
    def __init__(self, response_content: str):
        self.response_content = response_content
        self.called_with = []

    async def generate(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        self.called_with.append(messages)
        return LLMResponse(
            content=self.response_content,
            input_tokens=10,
            output_tokens=5,
            model="mock-model"
        )

class MockSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "mock_skill"

    @property
    def description(self) -> str:
        return "A mock skill for testing."

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        if arguments.get("fail"):
            return SkillResult(success=False, output="", error="Mock skill forced failure.")
        return SkillResult(success=True, output=f"Executed mock_skill with {arguments}")

@pytest.fixture
def mock_skill():
    return MockSkill()

@pytest.fixture
def clean_state():
    return AgentState(
        session_id="test-session",
        injected_skills=["mock_skill"]
    )

@pytest.fixture(autouse=True)
def disable_grill_me():
    from config.settings import settings
    original = settings.grill_me_enabled
    settings.grill_me_enabled = False
    yield
    settings.grill_me_enabled = original
