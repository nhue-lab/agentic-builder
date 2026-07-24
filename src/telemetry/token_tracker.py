class TokenTracker:
    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Approximates token count based on character length.
        Can be easily extended to use a real tokenizer like tiktoken.
        """
        if not text:
            return 0
        return (len(text) // 4) + 10
