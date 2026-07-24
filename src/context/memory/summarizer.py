import logging
from datetime import datetime, timezone
from src.context.state import Message
from src.lms.router import llm_router
from config.settings import settings

logger = logging.getLogger("agentic_builder.context.memory.summarizer")

class HistorySummarizer:
    @staticmethod
    async def summarize(messages_to_compress: list[Message]) -> Message:
        """
        Compresses a list of messages into a single system summary message.
        """
        if not messages_to_compress:
            return Message(
                role="system",
                content="No history to summarize.",
                timestamp=datetime.now(timezone.utc).isoformat(),
                priority=2
            )
            
        logger.info(f"HistorySummarizer: Summarizing {len(messages_to_compress)} messages.")
        
        history_text = "\n".join(
            f"[{msg.timestamp}] {msg.role.upper()}: {msg.content}"
            for msg in messages_to_compress
        )
        
        system_instruction = (
            "You are an expert context summarizer. Your job is to compress a conversation history "
            "between a user and an agent into a concise summary. Retain all key decisions, "
            "facts discovered, tools called, and results. Do not lose critical technical details "
            "or user constraints."
        )
        
        user_content = (
            "Please summarize the following conversation history:\n\n"
            f"{history_text}\n\n"
            "Summary:"
        )
        
        payload = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        try:
            response = await llm_router.generate(
                payload,
                model=settings.critique_model,
                temperature=0.1
            )
            summary_content = response.content.strip()
        except Exception as e:
            logger.error(f"HistorySummarizer failed: {str(e)}. Falling back to basic concatenation.")
            summary_content = "Fallback summary: " + "; ".join(
                f"{msg.role}: {msg.content[:50]}..." for msg in messages_to_compress
            )
            
        return Message(
            role="system",
            content=f"Summary of previous interactions:\n{summary_content}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            priority=2
        )
