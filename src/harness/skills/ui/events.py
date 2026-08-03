"""
UIEvent — Événements typés émis par l'agent vers le dashboard UI.

Architecture note : le schéma d'événements est INTENTIONNELLEMENT extensible
pour accueillir les spécificités de chaque famille de modèles (voir ROADMAP Jalon 2.5) :
  - Les modèles "thinking" (DeepSeek-R1, Claude Thinking, o1/o3) génèrent
    des reasoning tokens supplémentaires → type REASONING_TOKEN
  - Les champs `provider` et `model` permettent au dashboard d'afficher quel
    adapter LLM a répondu (primary Gemini vs fallback OpenAI, etc.)

Cela suit la règle cardinale du harness : cœur universel, adapters spécifiques au modèle.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import json


# ---------------------------------------------------------------------------
# Event Types
# ---------------------------------------------------------------------------
class UIEventType:
    ITERATION_START  = "ITERATION_START"   # Début d'une itération ReAct
    TOOL_CALL        = "TOOL_CALL"         # L'agent appelle un skill
    TOOL_RESULT      = "TOOL_RESULT"       # Résultat d'un skill
    AGENT_DONE       = "AGENT_DONE"        # Session terminée (success/fail)
    ERROR            = "ERROR"             # Erreur durant l'exécution
    REASONING_TOKEN  = "REASONING_TOKEN"   # [Thinking models] Tokens de raisonnement
                                           # (ex: blocs <think>...</think> de DeepSeek-R1)


# ---------------------------------------------------------------------------
# UIEvent Dataclass
# ---------------------------------------------------------------------------
@dataclass
class UIEvent:
    type: str
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Model-awareness fields (None si pas encore résolu par le router)
    provider: Optional[str] = None   # ex: "gemini", "openai", "anthropic"
    model: Optional[str] = None      # ex: "gemini-2.5-flash-lite", "gpt-4o"

    def to_sse(self) -> str:
        """Sérialise en format SSE : 'data: <json>\\n\\n'"""
        return f"data: {json.dumps(asdict(self))}\n\n"


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------
def make_iteration_start(iteration: int, max_iterations: int,
                          provider: Optional[str] = None,
                          model: Optional[str] = None) -> UIEvent:
    return UIEvent(
        type=UIEventType.ITERATION_START,
        payload={"iteration": iteration, "max_iterations": max_iterations},
        provider=provider,
        model=model,
    )


def make_tool_call(skill_name: str, arguments: dict,
                   thought: str,
                   provider: Optional[str] = None,
                   model: Optional[str] = None) -> UIEvent:
    return UIEvent(
        type=UIEventType.TOOL_CALL,
        payload={"skill_name": skill_name, "arguments": arguments, "thought": thought},
        provider=provider,
        model=model,
    )


def make_tool_result(skill_name: str, output: str, success: bool) -> UIEvent:
    return UIEvent(
        type=UIEventType.TOOL_RESULT,
        payload={"skill_name": skill_name, "output": output[:1000], "success": success},
    )


def make_agent_done(status: str, iterations: int, error: Optional[str] = None) -> UIEvent:
    return UIEvent(
        type=UIEventType.AGENT_DONE,
        payload={"status": status, "iterations": iterations, "error": error},
    )


def make_error(message: str, iteration: int) -> UIEvent:
    return UIEvent(
        type=UIEventType.ERROR,
        payload={"message": message, "iteration": iteration},
    )


def make_reasoning_token(content: str, iteration: int,
                          provider: Optional[str] = None,
                          model: Optional[str] = None) -> UIEvent:
    """
    Réservé aux thinking models (DeepSeek-R1, Claude Thinking, o1/o3).
    Le contenu est le texte brut entre les balises <think>...</think>
    ou l'équivalent selon le provider.
    """
    return UIEvent(
        type=UIEventType.REASONING_TOKEN,
        payload={"content": content, "iteration": iteration},
        provider=provider,
        model=model,
    )
