import logging
from src.context.state import Message
from src.context.memory.summarizer import HistorySummarizer

logger = logging.getLogger("agentic_builder.memory_window")

class MemoryWindow:
    def __init__(self, max_tokens: int = 400000):
        self.max_tokens = max_tokens

    def get_total_tokens(self, msgs: list[Message]) -> int:
        return sum(m.token_count if m.token_count is not None else ((len(m.content) // 4) + 10) for m in msgs)

    async def trim(self, messages: list[Message]) -> list[Message]:
        total_tokens = self.get_total_tokens(messages)
        if total_tokens <= self.max_tokens:
            return messages

        logger.info(f"Memory window exceeded ({total_tokens} approx tokens). Compressing oldest history.")

        # Preserving the immediate active context (last 4 messages)
        active_context_size = 4
        if len(messages) <= active_context_size + 1:
            # Too short to summarize safely, fallback to hard pruning
            return self._hard_prune(messages)

        system_msgs = [m for m in messages[:-active_context_size] if m.role == "system"]
        active_msgs = messages[-active_context_size:]
        candidates = [m for m in messages[:-active_context_size] if m.role != "system"]

        # Try to compress priority 0 (low) messages
        to_compress = [m for m in candidates if m.priority == 0]
        to_keep = [m for m in candidates if m.priority > 0]

        if to_compress:
            summary_msg = await HistorySummarizer.summarize(to_compress)
            new_history = system_msgs + [summary_msg] + to_keep + active_msgs
        else:
            # If no priority 0, try to compress priority 1 (medium)
            to_compress_p1 = [m for m in candidates if m.priority == 1]
            to_keep_p2 = [m for m in candidates if m.priority > 1]
            if to_compress_p1:
                summary_msg = await HistorySummarizer.summarize(to_compress_p1)
                new_history = system_msgs + [summary_msg] + to_keep_p2 + active_msgs
            else:
                new_history = system_msgs + candidates + active_msgs

        # Check if we still exceed limits. If so, fallback to hard pruning
        if self.get_total_tokens(new_history) > self.max_tokens:
            logger.warning("Context still exceeds limit after summarization. Applying hard pruning.")
            return self._hard_prune(new_history)

        return new_history

    def _hard_prune(self, messages: list[Message]) -> list[Message]:
        system_msgs = [m for m in messages if m.role == "system" or m.priority == 2]
        other_msgs = [m for m in messages if m.role != "system" and m.priority < 2]

        while other_msgs and self.get_total_tokens(system_msgs + other_msgs) > self.max_tokens:
            other_msgs.pop(0)

        return system_msgs + other_msgs
