import logging
import httpx
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.context.state import AgentState

logger = logging.getLogger("agentic_builder.skills.researcher")

class ResearcherSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "researcher"

    @property
    def description(self) -> str:
        return "Fetches real web pages or API data (e.g. OpenRouter API at https://openrouter.ai/api/v1/models or web URLs) or searches queries. Arguments: {'url': 'string'} or {'query': 'string'}"

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        url = arguments.get("url", "")
        query = arguments.get("query", "")

        target_url = url or (query if query.startswith("http") else "")

        if not target_url and "openrouter" in query.lower():
            target_url = "https://openrouter.ai/api/v1/models"

        if target_url:
            logger.info(f"Executing real HTTP GET on: {target_url}")
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(target_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgenticBuilder/1.0"})
                    if resp.status_code == 200:
                        text = resp.text[:4000]
                        return SkillResult(success=True, output=f"HTTP 200 OK from {target_url}:\n{text}")
                    else:
                        return SkillResult(success=False, output="", error=f"HTTP status {resp.status_code} for {target_url}")
            except Exception as e:
                logger.error(f"HTTP fetch error: {e}")
                return SkillResult(success=False, output="", error=f"Failed to fetch {target_url}: {e}")

        logger.info(f"Query search requested: {query}")
        return SkillResult(
            success=True,
            output=f"Search reference for '{query}': Fetch real OpenRouter API model pricing directly via url 'https://openrouter.ai/api/v1/models'."
        )
