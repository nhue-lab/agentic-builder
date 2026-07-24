import pytest
import httpx
from unittest.mock import AsyncMock, patch
from src.lms.router import LLMRouter, is_transient_error
from src.lms.base_client import LLMResponse

@pytest.mark.asyncio
async def test_router_primary_success():
    # Given a router with a mocked primary and fallback client
    router = LLMRouter()
    
    mock_response = LLMResponse(content="primary ok", input_tokens=10, output_tokens=5, model="gemini-mock")
    router.primary_client.generate = AsyncMock(return_value=mock_response)
    router.fallback_client.generate = AsyncMock()

    # When generate is called
    result = await router.generate([{"role": "user", "content": "hello"}])

    # Then it returns the primary client response and makes 1 attempt (0 retries)
    assert result.content == "primary ok"
    router.primary_client.generate.assert_called_once()
    router.fallback_client.generate.assert_not_called()


@pytest.mark.asyncio
async def test_router_transient_retry_success():
    # Given a router where primary fails once with a transient error, then succeeds
    router = LLMRouter()
    
    mock_response = LLMResponse(content="primary retry success", input_tokens=10, output_tokens=5, model="gemini-mock")
    router.primary_client.generate = AsyncMock(side_effect=[
        httpx.ConnectTimeout("Connection timed out"),
        mock_response
    ])
    router.fallback_client.generate = AsyncMock()

    # We patch the wait time in tenacity to avoid waiting in tests
    with patch("tenacity.nap.time.sleep", return_value=None):
        result = await router.generate([{"role": "user", "content": "hello"}])

    # Then it returns the response after 2 attempts, and fallback is not called
    assert result.content == "primary retry success"
    assert router.primary_client.generate.call_count == 2
    router.fallback_client.generate.assert_not_called()


@pytest.mark.asyncio
async def test_router_transient_exhausted_fallback():
    # Given a router where primary always fails with transient errors
    router = LLMRouter()
    
    router.primary_client.generate = AsyncMock(side_effect=[
        httpx.ConnectTimeout("Connection timed out 1"),
        httpx.ConnectTimeout("Connection timed out 2"),
        httpx.ConnectTimeout("Connection timed out 3"),
    ])
    fallback_response = LLMResponse(content="fallback ok", input_tokens=5, output_tokens=2, model="openai-mock")
    router.fallback_client.generate = AsyncMock(return_value=fallback_response)

    # We patch the wait time to run instantly
    with patch("tenacity.nap.time.sleep", return_value=None):
        result = await router.generate([{"role": "user", "content": "hello"}])

    # Then it makes 3 attempts on primary, then falls back to secondary
    assert result.content == "fallback ok"
    assert router.primary_client.generate.call_count == 3
    router.fallback_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_router_non_transient_immediate_fallback():
    # Given a router where primary fails with a non-transient error (e.g. ValueError)
    router = LLMRouter()
    
    router.primary_client.generate = AsyncMock(side_effect=ValueError("Invalid parameter value"))
    fallback_response = LLMResponse(content="fallback ok", input_tokens=5, output_tokens=2, model="openai-mock")
    router.fallback_client.generate = AsyncMock(return_value=fallback_response)

    result = await router.generate([{"role": "user", "content": "hello"}])

    # Then it fails immediately without retrying, and triggers fallback
    assert result.content == "fallback ok"
    assert router.primary_client.generate.call_count == 1
    router.fallback_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_router_all_failed_raises():
    # Given a router where both primary and fallback fail
    router = LLMRouter()
    
    router.primary_client.generate = AsyncMock(side_effect=ValueError("Primary failed"))
    router.fallback_client.generate = AsyncMock(side_effect=RuntimeError("Fallback failed"))

    # When calling generate, it should propagate the fallback error
    with pytest.raises(RuntimeError) as exc_info:
        await router.generate([{"role": "user", "content": "hello"}])
        
    assert "Fallback failed" in str(exc_info.value)
    assert router.primary_client.generate.call_count == 1
    router.fallback_client.generate.assert_called_once()


def test_is_transient_error_classification():
    # 1. HTTPX transient errors
    assert is_transient_error(httpx.ConnectTimeout("timeout")) is True
    assert is_transient_error(httpx.ReadTimeout("timeout")) is True
    assert is_transient_error(httpx.RequestError("network error")) is True
    
    # 2. HTTPX status codes
    response_429 = httpx.Response(status_code=429, request=httpx.Request("GET", "http://test"))
    response_500 = httpx.Response(status_code=500, request=httpx.Request("GET", "http://test"))
    response_400 = httpx.Response(status_code=400, request=httpx.Request("GET", "http://test"))
    
    assert is_transient_error(httpx.HTTPStatusError("Rate Limit", request=httpx.Request("GET", "http://test"), response=response_429)) is True
    assert is_transient_error(httpx.HTTPStatusError("Internal Server Error", request=httpx.Request("GET", "http://test"), response=response_500)) is True
    assert is_transient_error(httpx.HTTPStatusError("Bad Request", request=httpx.Request("GET", "http://test"), response=response_400)) is False

    # 3. Python standard timeout
    assert is_transient_error(TimeoutError("Python timeout")) is True

    # 4. Third-party provider errors with status code or keywords
    class MockOpenAIRateLimitError(Exception):
        status_code = 429
    
    assert is_transient_error(MockOpenAIRateLimitError("Too Many Requests")) is True
    
    class MockGoogleAPIError(Exception):
        pass
    
    # Keyword detection in message
    assert is_transient_error(MockGoogleAPIError("Quota exceeded for this project")) is True
    assert is_transient_error(MockGoogleAPIError("Resource has been exhausted")) is True
    assert is_transient_error(MockGoogleAPIError("Rate limit reached")) is True
    assert is_transient_error(MockGoogleAPIError("Some other permanent API error")) is False
