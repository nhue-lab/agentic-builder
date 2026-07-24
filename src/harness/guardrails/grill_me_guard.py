import logging
from datetime import datetime, timezone
from src.context.state import AgentState, AgentStatus, Message
from src.loop.hitl.impact_report import ImpactReport
from src.lms.router import llm_router
from config.settings import settings

logger = logging.getLogger("agentic_builder.guardrails.grill_me_guard")

class GrillMeGuard:
    @classmethod
    async def intercept(cls, task: str, state: AgentState) -> AgentState:
        # Check if we should skip
        if not settings.grill_me_enabled:
            logger.info("GrillMeGuard is disabled in settings.")
            return state

        # If it's already approved, transition to RUNNING and continue
        if state.status == AgentStatus.GRILL_ME_APPROVED:
            logger.info("Task already approved by /grill-me. Resuming agent run.")
            state.status = AgentStatus.RUNNING
            return state

        # Only intercept on the first attempt and the very first iteration
        if state.task_attempt > 1 or state.iteration > 0:
            return state

        logger.info("Intercepting run to perform /grill-me semantic impact analysis.")
        
        prompt = (
            f"Génère un rapport d'impact sémantique détaillé pour la tâche suivante :\n"
            f"\"{task}\"\n\n"
            f"Remplis avec précision les champs du schéma de réponse en analysant "
            f"l'objectif, les fichiers qui pourraient être modifiés ou créés, les risques techniques, de sécurité ou de coûts "
            f"et comment nos guardrails (comme la restriction de sandbox de chemin, etc.) les limitent."
        )
        
        messages_payload = [
            {"role": "system", "content": "Tu es un assistant de sécurité technique. Tu dois générer des rapports d'impact au format JSON structuré."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Generate the report using the critique model (usually a faster Flash model)
            llm_response = await llm_router.generate(
                messages_payload,
                response_schema=ImpactReport,
                temperature=settings.temperature
            )
            report = ImpactReport.model_validate_json(llm_response.content)
        except Exception as e:
            logger.error(f"Failed to generate or validate ImpactReport: {e}")
            # Fallback mock report
            report = ImpactReport(
                objective=f"Exécuter la tâche : {task}",
                files_affected=["A déterminer pendant l'exécution"],
                risks=["Risque de génération de code incorrect", "Risque d'épuisement de quota API"],
                guardrails=["Harnais d'exécution ReAct avec critique de code", "Limiteur de tokens/contexte"]
            )

        # Save to disk (.agent/impact_report.json)
        report.save()

        # Update agent state to wait for human validation
        state.status = AgentStatus.WAITING_FOR_HUMAN
        
        # Add message to history
        state.history.append(Message(
            role="system",
            content=f"Observation: [GRILL-ME REPORT GENERATED]\n{report.model_dump_json()}",
            timestamp=datetime.now(timezone.utc).isoformat()
        ))

        # Print report in terminal
        print(report.to_terminal())

        return state
