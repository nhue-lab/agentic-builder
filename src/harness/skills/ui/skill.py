"""
UISkill — Skill optionnel pour lancer un dashboard web local et émettre
des événements temps réel depuis la boucle ReAct.

Comportement :
  - Si FastAPI/uvicorn ne sont pas installés → graceful degradation (warning, pas d'exception)
  - Si `ui_enabled: false` dans agent_config.json → skill inactive (no-op)
  - Le serveur tourne dans un thread daemon séparé pour ne pas bloquer la boucle asyncio

Intégration dans le harness :
  - L'agent NE liste PAS "ui" dans injected_skills (ce n'est pas un skill appelable par le LLM)
  - UISkill est un composant infra injecté directement dans AgentEngine
  - L'engine appelle `emit_event()` après chaque itération (pattern Observer)
"""
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional

from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.harness.skills.ui.events import UIEvent
from src.harness.skills.ui.bus import UIEventBus
from src.context.state import AgentState

logger = logging.getLogger("agentic_builder.ui.skill")

_UI_SERVER_THREAD: Optional[threading.Thread] = None
_UI_SERVER_STARTED = False
_TEMPLATES_DIR = Path(__file__).parent / "templates"


class UISkill(BaseSkill):
    """
    Composant infra (non-LLM-callable) pour le dashboard web local.

    Responsabilités :
    1. Lancer le serveur FastAPI SSE en arrière-plan (une seule fois)
    2. Émettre des UIEvents vers les clients SSE connectés
    3. Ouvrir le navigateur automatiquement au premier lancement
    """

    def __init__(self, port: int = 7860, auto_open_browser: bool = True):
        self.port = port
        self.auto_open_browser = auto_open_browser
        self._server_available = False
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Vérifie si FastAPI + uvicorn sont disponibles (graceful degradation)."""
        try:
            import fastapi  # noqa: F401
            import uvicorn  # noqa: F401
            self._server_available = True
        except ImportError:
            logger.warning(
                "UISkill: FastAPI ou uvicorn non installé. "
                "Le dashboard UI est désactivé. "
                "Pour l'activer : `uv add fastapi uvicorn[standard]`"
            )
            self._server_available = False

    # ------------------------------------------------------------------
    # BaseSkill interface (no-op : UISkill n'est pas appelable par le LLM)
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return "ui"

    @property
    def description(self) -> str:
        return "Internal infrastructure skill — not callable by the LLM agent."

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        # UISkill n'est pas exposée au LLM ; ce point d'entrée ne doit pas être atteint.
        return SkillResult(success=False, output="UISkill is not directly callable by the agent.")

    # ------------------------------------------------------------------
    # Public API — utilisée par AgentEngine
    # ------------------------------------------------------------------
    def launch_server(self) -> None:
        """
        Lance le serveur FastAPI en arrière-plan (thread daemon).
        Idempotent : un seul serveur par process.
        Ouvre le navigateur automatiquement si `auto_open_browser=True`.
        """
        global _UI_SERVER_THREAD, _UI_SERVER_STARTED

        if not self._server_available:
            return

        if _UI_SERVER_STARTED:
            logger.debug("UISkill: server already running, skipping launch.")
            return

        _UI_SERVER_STARTED = True
        _UI_SERVER_THREAD = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="ui-dashboard-server"
        )
        _UI_SERVER_THREAD.start()
        logger.info(f"UISkill: dashboard started → http://localhost:{self.port}")

        if self.auto_open_browser:
            # Petit délai pour laisser uvicorn démarrer avant d'ouvrir le navigateur
            threading.Timer(1.5, self._open_browser).start()

    def _run_server(self) -> None:
        """Thread target : lance uvicorn dans sa propre event loop."""
        try:
            import uvicorn
            from src.entrypoints.web_ui import create_app
            app = create_app(templates_dir=_TEMPLATES_DIR)
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=self.port,
                log_level="warning",  # Silencieux — les logs UI ne doivent pas polluer le terminal
                access_log=False,
            )
        except Exception as e:
            logger.error(f"UISkill: server crashed — {e}")

    def _open_browser(self) -> None:
        try:
            import webbrowser
            webbrowser.open(f"http://localhost:{self.port}")
        except Exception:
            pass

    async def emit_event(self, event: UIEvent) -> None:
        """
        Publie un UIEvent vers tous les clients SSE connectés.
        No-op si le serveur n'est pas disponible.
        """
        if not self._server_available:
            return
        await UIEventBus.publish(event)
