import re

class InputFilter:
    INJECTION_PATTERNS = [
        r"ignore\s+the\s+previous\s+instructions",
        r"ignore\s+above\s+instructions",
        r"system\s+override",
        r"you\s+must\s+now\s+act\s+as",
        r"bypass\s+security"
    ]

    @classmethod
    def is_safe(cls, text: str) -> bool:
        lowered = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                return False
        return True
