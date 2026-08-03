"""
UIEventBus — Bus d'événements asyncio partagé entre la boucle ReAct et le serveur SSE.

Pattern : singleton par instance de process.
La boucle ReAct publie via `UIEventBus.publish(event)`.
L'endpoint SSE consomme via `UIEventBus.subscribe()` (itérateur async).

Note de design : on utilise asyncio.Queue avec maxsize pour éviter une accumulation
mémoire illimitée si le client SSE déconnecte — les events les plus anciens
sont droppés avec un warning (non-bloquant pour la boucle ReAct).
"""
import asyncio
import logging
from typing import AsyncIterator
from src.harness.skills.ui.events import UIEvent

logger = logging.getLogger("agentic_builder.ui.bus")

_MAX_QUEUE_SIZE = 200  # ~200 events max en buffer, évite les fuites mémoire


class UIEventBus:
    """
    Singleton thread-safe (asyncio) pour le pub/sub d'UIEvents.
    Supporte N subscribers (un par connexion SSE active).
    """
    _subscribers: list[asyncio.Queue] = []

    @classmethod
    async def publish(cls, event: UIEvent) -> None:
        """
        Publie un événement à tous les subscribers SSE connectés.
        Non-bloquant : si un subscriber est plein, l'événement est ignoré
        pour lui (graceful degradation — la boucle ReAct ne stalle jamais).
        """
        dead = []
        for q in cls._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    f"UIEventBus: subscriber queue full (maxsize={_MAX_QUEUE_SIZE}), "
                    "dropping event for this subscriber."
                )
            except Exception as e:
                logger.error(f"UIEventBus: unexpected error publishing event: {e}")
                dead.append(q)
        for q in dead:
            cls._subscribers.remove(q)

    @classmethod
    def subscribe(cls) -> asyncio.Queue:
        """
        Crée et enregistre une nouvelle Queue pour un subscriber SSE.
        Retourne la Queue — le caller l'itère en async.
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE_SIZE)
        cls._subscribers.append(q)
        logger.info(f"UIEventBus: new SSE subscriber connected (total={len(cls._subscribers)})")
        return q

    @classmethod
    def unsubscribe(cls, q: asyncio.Queue) -> None:
        """Désenregistre un subscriber (appelé à la déconnexion SSE)."""
        try:
            cls._subscribers.remove(q)
            logger.info(f"UIEventBus: SSE subscriber disconnected (total={len(cls._subscribers)})")
        except ValueError:
            pass

    @classmethod
    async def stream(cls, q: asyncio.Queue) -> AsyncIterator[UIEvent]:
        """
        Itérateur async pour consommer les events d'un subscriber.
        À utiliser dans l'endpoint SSE avec `async for event in UIEventBus.stream(q)`.
        """
        try:
            while True:
                event = await q.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            cls.unsubscribe(q)
