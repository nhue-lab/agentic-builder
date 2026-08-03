"""
web_ui.py — Entrypoint FastAPI pour le dashboard de monitoring temps réel.

Routes :
  GET /          → Dashboard HTML (servi depuis templates/index.html)
  GET /events    → Flux SSE des UIEvents de la boucle ReAct
  GET /health    → Healthcheck JSON

Architecture SSE :
  Le client JS (EventSource) se connecte à /events.
  Le serveur stream les UIEvents depuis UIEventBus via asyncio.Queue.
  Chaque événement est sérialisé en JSON et envoyé comme `data: <json>\\n\\n`.

Non-bloquant : le serveur tourne dans un thread daemon géré par UISkill.
La boucle ReAct principale n'est jamais affectée.
"""
import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator

logger = logging.getLogger("agentic_builder.ui.server")


def create_app(templates_dir: Path):
    """
    Factory FastAPI — importée conditionnellement par UISkill._run_server().
    Séparée de l'import-time pour permettre la graceful degradation.
    """
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as e:
        raise ImportError(
            "FastAPI est requis pour le dashboard UI. "
            "Installez-le avec : `uv add fastapi uvicorn[standard]`"
        ) from e

    from src.harness.skills.ui.bus import UIEventBus

    app = FastAPI(
        title="Agentic Builder — Dashboard",
        description="Monitoring temps réel de la boucle ReAct",
        version="1.0.0",
        docs_url=None,   # Pas de Swagger UI (dashboard suffit)
        redoc_url=None,
    )

    # ------------------------------------------------------------------
    # GET / — Dashboard HTML
    # ------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        html_path = templates_dir / "index.html"
        if not html_path.exists():
            return HTMLResponse(
                "<h1>Dashboard template not found</h1>"
                f"<p>Expected: {html_path}</p>",
                status_code=500
            )
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # GET /events — SSE Stream
    # ------------------------------------------------------------------
    @app.get("/events")
    async def sse_events(request: Request):
        """
        Endpoint SSE : stream les UIEvents vers le client JS.

        Protocol :
          - Content-Type: text/event-stream
          - Chaque message : `data: <json>\\n\\n`
          - Keepalive : commentaire `: keepalive\\n\\n` toutes les 15s
            pour prévenir les timeouts proxy/navigateur.
        """
        queue = UIEventBus.subscribe()

        async def event_generator() -> AsyncIterator[str]:
            keepalive_interval = 15  # secondes
            try:
                while True:
                    # Attente de l'événement suivant avec timeout keepalive
                    try:
                        event = await asyncio.wait_for(
                            queue.get(),
                            timeout=keepalive_interval
                        )
                        yield event.to_sse()
                    except asyncio.TimeoutError:
                        # Keepalive SSE (commentaire, ignoré par EventSource)
                        yield ": keepalive\n\n"
                    # Détection de déconnexion client
                    if await request.is_disconnected():
                        logger.info("SSE client disconnected.")
                        break
            except asyncio.CancelledError:
                pass
            finally:
                UIEventBus.unsubscribe(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Désactive le buffering Nginx
                "Connection": "keep-alive",
            }
        )

    # ------------------------------------------------------------------
    # GET /health — Healthcheck
    # ------------------------------------------------------------------
    @app.get("/health")
    async def health():
        return JSONResponse({
            "status": "ok",
            "service": "agentic-builder-ui",
            "subscribers": len(UIEventBus._subscribers)
        })

    return app
