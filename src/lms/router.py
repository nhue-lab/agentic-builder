from typing import Any, Optional
import logging
import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception
from src.lms.base_client import BaseLLMClient, LLMResponse
from src.lms.providers.gemini_client import GeminiClient
from src.lms.providers.openai_client import OpenAIClient
from config.settings import settings

logger = logging.getLogger("agentic_builder.lms_router")

def is_transient_error(exception: Exception) -> bool:
    """
    Identifie si une exception est une erreur temporaire / transitoire
    (timeout, quota/rate limit, erreur 5xx, erreur réseau).
    """
    # 1. Erreurs réseau et timeouts de httpx
    if isinstance(exception, (httpx.RequestError, httpx.TimeoutException)):
        logger.warning(f"Transient HTTPX error detected: {type(exception).__name__} - {exception}")
        return True

    # 2. Codes d'état HTTP temporaires (429 ou 5xx)
    if isinstance(exception, httpx.HTTPStatusError):
        if exception.response.status_code == 429 or exception.response.status_code >= 500:
            logger.warning(f"Transient HTTP status error detected: {exception.response.status_code}")
            return True
        return False

    # 3. Timeouts généraux Python
    if isinstance(exception, TimeoutError):
        logger.warning("Transient Python TimeoutError detected")
        return True

    # 4. Erreurs d'API de fournisseurs tiers (Google GenAI, OpenAI, etc.)
    exc_name = type(exception).__name__
    exc_module = type(exception).__module__.lower()

    # Détection par mot-clé et type de statut (ex: rate limit, quota, timeout)
    is_provider_error = "google" in exc_module or "openai" in exc_module or "google" in exc_name.lower() or "openai" in exc_name.lower()
    if is_provider_error:
        # Essayer de récupérer le code de statut s'il existe
        status_code = getattr(exception, "status_code", getattr(exception, "code", None))
        if status_code in (429, 500, 503, 504):
            logger.warning(f"Transient provider error detected via status code {status_code}: {exc_name}")
            return True
        
        # Vérification textuelle de l'erreur
        msg = str(exception).lower()
        transient_keywords = ["quota", "rate limit", "rate_limit", "timeout", "exhausted", "500", "503", "504", "temporarily unavailable"]
        if any(kw in msg for kw in transient_keywords):
            logger.warning(f"Transient provider error detected via message: {exc_name} - {msg}")
            return True

    return False

class LLMRouter:
    def __init__(self):
        self.primary_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model_name=settings.model
        )
        self.fallback_client = OpenAIClient(
            api_key=settings.openai_api_key,
            model_name=settings.fallback_model
        )

    async def generate(
        self, 
        messages: list[dict[str, str]], 
        response_schema: Optional[Any] = None, 
        **kwargs
    ) -> LLMResponse:
        logger.info(f"Routing request. Primary client: {settings.model}")
        try:
            # We attempt the primary model with a resilient retry mechanism for transient errors.
            # 3 attempts (initial attempt + 2 retries), exponential backoff: start 2s, max 10s.
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=2, max=10),
                retry=retry_if_exception(is_transient_error),
                reraise=True
            ):
                with attempt:
                    if attempt.retry_state.attempt_number > 1:
                        logger.info(f"Retrying primary client call (attempt {attempt.retry_state.attempt_number})")
                    response = await self.primary_client.generate(messages, response_schema=response_schema, **kwargs)
                    return response
        except Exception as e:
            logger.warning(f"Primary client failed after all retries or with a non-transient exception: {str(e)}. Attempting fallback client: {settings.fallback_model}")
            try:
                response = await self.fallback_client.generate(messages, response_schema=response_schema, **kwargs)
                return response
            except Exception as fe:
                logger.error(f"Fallback client also failed: {str(fe)}")
                raise fe
        
# Singleton LLMRouter instance
llm_router = LLMRouter()

