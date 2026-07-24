import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from src.context.state import Message
from src.context.memory.window import MemoryWindow
from src.context.memory.summarizer import HistorySummarizer
from src.lms.base_client import LLMResponse

@pytest.mark.asyncio
async def test_memory_window_get_total_tokens():
    window = MemoryWindow(max_tokens=1000)
    messages = [
        # Content length is 20, token_count will default to (20 // 4) + 10 = 15
        Message(role="system", content="A message of size 20", timestamp="1"),
        # Explicit token count = 100
        Message(role="user", content="Short", timestamp="2", token_count=100)
    ]
    total = window.get_total_tokens(messages)
    assert total == 115

@pytest.mark.asyncio
async def test_memory_window_no_trim():
    window = MemoryWindow(max_tokens=1000)
    messages = [
        Message(role="system", content="System instruction", timestamp="1"),
        Message(role="user", content="User request", timestamp="2")
    ]
    trimmed = await window.trim(messages)
    assert len(trimmed) == 2
    assert trimmed == messages

@pytest.mark.asyncio
async def test_memory_window_too_short_to_summarize_falls_back_to_hard_prune():
    # max_tokens is very low, message count is 4 (<= active_context_size + 1 = 5)
    window = MemoryWindow(max_tokens=30)
    messages = [
        Message(role="system", content="System instruction", timestamp="1"), # priority 2 (kept)
        Message(role="user", content="First query", timestamp="2"),          # priority 0 (pruned)
        Message(role="assistant", content="Answer", timestamp="3"),          # priority 0 (pruned)
        Message(role="user", content="Second query", timestamp="4"),         # priority 0 (kept because other_msgs is pruned until it fits)
    ]
    
    trimmed = await window.trim(messages)
    # System instruction (priority 2) is kept.
    assert any(m.role == "system" for m in trimmed)
    # The total tokens should be <= 30
    assert window.get_total_tokens(trimmed) <= 30

@pytest.mark.asyncio
async def test_memory_window_compress_priority_0_messages():
    window = MemoryWindow(max_tokens=100)
    
    # 8 messages total, allowing active_context_size = 4
    # The first 4 (excluding system) are candidate for compression
    messages = [
        Message(role="system", content="System prompt", timestamp="1"),               # priority 2 (system)
        Message(role="user", content="Observation: text", timestamp="2"),            # priority 1 (observation)
        Message(role="user", content="Priority 0 text a", timestamp="3"),            # priority 0
        Message(role="assistant", content="Priority 0 text b", timestamp="4"),       # priority 0
        
        # Last 4 (active context - preserved)
        Message(role="user", content="Active 1", timestamp="5"),
        Message(role="assistant", content="Active 2", timestamp="6"),
        Message(role="user", content="Active 3", timestamp="7"),
        Message(role="assistant", content="Active 4", timestamp="8"),
    ]
    
    # Let's mock the HistorySummarizer to avoid LLM calls
    mock_summary_msg = Message(
        role="system",
        content="Summary of previous interactions:\nSimulated summary content",
        timestamp="now",
        priority=2
    )
    
    with patch.object(HistorySummarizer, "summarize", AsyncMock(return_value=mock_summary_msg)) as mock_sum:
        trimmed = await window.trim(messages)
        
        # HistorySummarizer.summarize should be called with the priority 0 messages
        mock_sum.assert_called_once()
        called_args = mock_sum.call_args[0][0]
        # Should compress only candidates with priority 0
        assert all(m.priority == 0 for m in called_args)
        assert len(called_args) == 2
        assert called_args[0].content == "Priority 0 text a"
        assert called_args[1].content == "Priority 0 text b"

        # The resulting trimmed list should contain:
        # system_msgs + [summary_msg] + to_keep (priority > 0 candidates) + active_msgs
        # system_msgs: System prompt (1)
        # summary_msg: mock_summary_msg
        # to_keep: Observation: text (2)
        # active_msgs: Active 1 (5), Active 2 (6), Active 3 (7), Active 4 (8)
        assert len(trimmed) == 7
        assert trimmed[0].content == "System prompt"
        assert "Simulated summary content" in trimmed[1].content
        assert trimmed[2].content == "Observation: text"
        assert trimmed[3].content == "Active 1"

@pytest.mark.asyncio
async def test_memory_window_compress_priority_1_messages():
    window = MemoryWindow(max_tokens=80)
    
    # Candidates contain no priority 0 (only priority 1)
    messages = [
        Message(role="system", content="System prompt", timestamp="1"),               # priority 2 (system)
        Message(role="user", content="Observation: one", timestamp="2"),             # priority 1 (observation)
        Message(role="user", content="Observation: two", timestamp="3"),             # priority 1 (observation)
        
        # Last 4 (active context - preserved)
        Message(role="user", content="Active 1", timestamp="4"),
        Message(role="assistant", content="Active 2", timestamp="5"),
        Message(role="user", content="Active 3", timestamp="6"),
        Message(role="assistant", content="Active 4", timestamp="7"),
    ]
    
    mock_summary_msg = Message(
        role="system",
        content="Summary of previous interactions:\nSimulated summary content",
        timestamp="now",
        priority=2
    )
    
    with patch.object(HistorySummarizer, "summarize", AsyncMock(return_value=mock_summary_msg)) as mock_sum:
        trimmed = await window.trim(messages)
        mock_sum.assert_called_once()
        called_args = mock_sum.call_args[0][0]
        # Should compress only candidates with priority 1
        assert all(m.priority == 1 for m in called_args)
        assert len(called_args) == 2

@pytest.mark.asyncio
async def test_history_summarizer_empty():
    summary = await HistorySummarizer.summarize([])
    assert summary.role == "system"
    assert summary.content == "No history to summarize."
    assert summary.priority == 2

@pytest.mark.asyncio
async def test_history_summarizer_llm_success():
    messages = [
        Message(role="user", content="Hello, tell me a joke", timestamp="1"),
        Message(role="assistant", content="Why did the chicken cross the road?", timestamp="2")
    ]
    
    mock_llm_response = LLMResponse(
        content="The user asked for a joke and the assistant told a chicken joke.",
        input_tokens=10,
        output_tokens=5,
        model="mock-model"
    )
    
    with patch("src.context.memory.summarizer.llm_router.generate", AsyncMock(return_value=mock_llm_response)) as mock_generate:
        summary = await HistorySummarizer.summarize(messages)
        
        mock_generate.assert_called_once()
        assert summary.role == "system"
        assert "The user asked for a joke" in summary.content
        assert summary.priority == 2

@pytest.mark.asyncio
async def test_history_summarizer_llm_fallback():
    messages = [
        Message(role="user", content="Hello", timestamp="1"),
        Message(role="assistant", content="Hi there", timestamp="2")
    ]
    
    # Simulate an API error
    with patch("src.context.memory.summarizer.llm_router.generate", AsyncMock(side_effect=RuntimeError("API Error"))):
        summary = await HistorySummarizer.summarize(messages)
        
        assert summary.role == "system"
        # Falls back to basic concatenation
        assert "Fallback summary" in summary.content
        assert "user: Hello..." in summary.content
        assert "assistant: Hi there..." in summary.content
