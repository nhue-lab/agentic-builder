import os
import sys
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from src.context.state import AgentState, AgentStatus
from config.settings import settings

logger = logging.getLogger("agentic_builder.entrypoints.telegram_bot")

class TelegramBotAdapter:
    def __init__(self, token: str, allowed_users: list[str]):
        self.token = token
        self.allowed_users = [str(u).strip().lower() for u in allowed_users if str(u).strip()]
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def is_authorized(self, user_id: int, username: str) -> bool:
        if not self.allowed_users:
            # If whitelist is empty, reject all by security default
            return False
        str_id = str(user_id).lower()
        str_user = (username or "").lower()
        return str_id in self.allowed_users or str_user in self.allowed_users or f"@{str_user}" in self.allowed_users

    async def send_typing(self, client: httpx.AsyncClient, chat_id: int):
        try:
            await client.post(f"{self.base_url}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})
        except Exception as e:
            logger.warning(f"Failed to send typing status: {e}")

    async def send_message(self, client: httpx.AsyncClient, chat_id: int, text: str):
        # Chunk message if exceeds Telegram 4096 char limit
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            try:
                await client.post(f"{self.base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                })
            except Exception:
                # Fallback without Markdown parsing if syntax error in markdown
                await client.post(f"{self.base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": chunk
                })

    async def process_message(self, client: httpx.AsyncClient, message: dict):
        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        user_id = from_user.get("id")
        username = from_user.get("username", "")
        text = message.get("text", "").strip()

        if not text:
            return

        # Security Whitelist check
        if not self.is_authorized(user_id, username):
            logger.warning(f"Unauthorized Telegram access attempt from user_id {user_id} (@{username})")
            await self.send_message(
                client, 
                chat_id, 
                "⛔ *Accès Refusé* : Votre compte Telegram n'est pas dans la liste autorisée (`ALLOWED_TELEGRAM_USERS`)."
            )
            return

        # Commands handling
        if text == "/start" or text == "/help":
            welcome_msg = (
                "🤖 *Agentic Builder Bot (Render Cloud Active)*\n\n"
                "Commandes disponibles :\n"
                "- `/status` : Vérifier l'état de l'agent\n"
                "- `/approve` : Approuver la phase `/grill-me` (déverrouiller l'exécution)\n"
                "- Envoyez simplement une tâche pour démarrer le cadrage."
            )
            await self.send_message(client, chat_id, welcome_msg)
            return

        session_id = f"telegram_{chat_id}"
        
        # Load or initialize AgentState
        state_file = f".agent/state_{chat_id}.json"
        state = None
        if os.path.exists(state_file):
            try:
                state = AgentState.load_from_file(state_file)
            except Exception:
                state = None

        if not state:
            state = AgentState(
                session_id=session_id,
                injected_skills=["researcher", "tester", "subagent"]
            )

        if text == "/approve":
            state.status = AgentStatus.GRILL_ME_APPROVED
            await self.send_message(client, chat_id, "✅ *Phase /grill-me approuvée !* Le verrou Read-Only est levé. Traitement en cours...")

        if text == "/status":
            await self.send_message(client, chat_id, f"📊 *Statut Agent* : `{state.status.value}` (Iter: {state.iteration})")
            return

        # Send typing action
        await self.send_typing(client, chat_id)

        # Run Engine
        from src.loop.engine import AgentEngine
        from src.loop.router import LoopRouter
        from src.harness.skills.researcher.skill import ResearcherSkill
        from src.harness.skills.tester.skill import TesterSkill
        from src.harness.skills.subagent.subagent_skill import SubAgentSkill

        skills = {
            "researcher": ResearcherSkill(),
            "tester": TesterSkill(),
            "subagent": SubAgentSkill()
        }
        router = LoopRouter(skills=skills)
        engine = AgentEngine(router)

        try:
            res_state = await engine.run(text, state)
            
            # Save state
            os.makedirs(".agent", exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(res_state.model_dump_json(indent=2))

            if res_state.status == AgentStatus.WAITING_FOR_HUMAN:
                # Check for ImpactReport output
                from src.loop.hitl.impact_report import ImpactReport
                report = ImpactReport.load()
                report_str = report.to_terminal() if report else "Rapport d'impact généré."
                await self.send_message(
                    client,
                    chat_id,
                    f"🔥 *RAPPORT /GRILL-ME PHASE 0*\n\n```text\n{report_str}\n```\n\n👉 Tapez `/approve` pour valider et lancer l'exécution."
                )
            else:
                proposed = res_state.metadata.get("proposed_response", "Tâche exécutée.")
                await self.send_message(client, chat_id, proposed)

        except PermissionError as pe:
            await self.send_message(client, chat_id, f"🔒 *Verrou Sécurité* : {str(pe)}\n\nTapez `/approve` pour valider le cadrage `/grill-me`.")
        except Exception as e:
            logger.error(f"Error running engine via Telegram: {e}")
            await self.send_message(client, chat_id, f"⚠️ *Erreur d'exécution* : {str(e)}")

    async def start_polling(self):
        logger.info("Starting Telegram Bot Long-Polling adapter...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                try:
                    res = await client.get(f"{self.base_url}/getUpdates", params={"offset": self.offset, "timeout": 20})
                    if res.status_code == 200:
                        data = res.json()
                        for result in data.get("result", []):
                            self.offset = result["update_id"] + 1
                            if "message" in result:
                                await self.process_message(client, result["message"])
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error in Telegram Polling loop: {e}")
                    await asyncio.sleep(5)

def run_telegram_bot():
    token = settings.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    allowed_str = settings.allowed_telegram_users or os.getenv("ALLOWED_TELEGRAM_USERS", "").split(",")
    
    if not token:
        print("❌ Erreur : TELEGRAM_BOT_TOKEN non configuré dans .env")
        sys.exit(1)

    adapter = TelegramBotAdapter(token=token, allowed_users=allowed_str)
    asyncio.run(adapter.start_polling())

if __name__ == "__main__":
    run_telegram_bot()
