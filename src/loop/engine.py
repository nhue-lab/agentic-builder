import logging
from datetime import datetime, timezone
from src.context.state import AgentState, AgentStatus, Message, LLMDecision
from src.prompt.formatter import PromptFormatter
from src.lms.router import llm_router
from src.harness.guardrails.input_filter import InputFilter
from src.harness.guardrails.output_filter import OutputFilter
from src.loop.router import LoopRouter
from src.loop.recovery import LoopRecovery
from src.context.memory.window import MemoryWindow
from config.settings import settings

logger = logging.getLogger("agentic_builder.loop.engine")

class AgentEngine:
    def __init__(self, router: LoopRouter):
        self.router = router
        self.memory_window = MemoryWindow(max_tokens=settings.max_tokens_per_session)

    async def run(self, task: str, state: AgentState) -> AgentState:
        logger.info(f"Starting AgentEngine job {state.session_id} with task: {task}")
        state.status = AgentStatus.RUNNING

        from src.telemetry.metrics import SessionMetrics
        metrics = SessionMetrics(state.session_id)
        metrics.log_event("run_start", {"task": task})

        # Trajectory collection
        from src.telemetry.trajectory import TrajectoryLogger, TrajectoryStep
        trajectory_steps: list[TrajectoryStep] = []

        # Episodic Memory recall
        if settings.episodic_memory_enabled:
            from src.context.memory.memory_store import EpisodicMemoryStore
            memory_store = EpisodicMemoryStore(db_path=settings.memory_db_path)
            memories = memory_store.recall(task, top_k=settings.memory_top_k)
            if memories:
                memory_text = "\n".join([f"- Souvenir ({m.timestamp[:10]}): {m.content}" for m in memories])
                state.history.append(Message(
                    role="system",
                    content=f"Contextual memories recalled from previous sessions:\n{memory_text}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    priority=2
                ))
                logger.info(f"Recalled {len(memories)} memories for task.")

        # Add initial instructions/user request to state if history is empty
        if not state.history:
            # We fetch system prompt from templates
            from src.prompt.schema_injector import SchemaInjector
            decision_schema = SchemaInjector.get_json_schema(LLMDecision)
            system_prompt = PromptFormatter.render_template(
                settings.system_prompt_path,
                {
                    "available_skills": ", ".join(state.injected_skills),
                    "response_schema": decision_schema
                }
            )
            state.history.append(Message(role="system", content=system_prompt, timestamp=datetime.now(timezone.utc).isoformat()))
            state.history.append(Message(role="user", content=task, timestamp=datetime.now(timezone.utc).isoformat()))

        # Check input safety
        if not InputFilter.is_safe(task):
            logger.warning("Input request was flagged by input filter!")
            state.status = AgentStatus.FAILED
            state.errors.append("Input violation: potential prompt injection.")
            metrics.log_event("input_safety_violation", {"task": task})
            
            # Finalize metrics
            metrics.finalize(
                final_status=state.status.value,
                total_iterations=0,
                total_errors=len(state.errors),
                critique_scores=state.critique_scores,
                model=settings.model
            )
            return state

        # Call GrillMeGuard interceptor
        from src.harness.guardrails.grill_me_guard import GrillMeGuard
        state = await GrillMeGuard.intercept(task, state)
        if state.status == AgentStatus.WAITING_FOR_HUMAN:
            # Persist state and exit early
            import os
            os.makedirs(".agent", exist_ok=True)
            with open(".agent/state.json", "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
            
            metrics.finalize(
                final_status=state.status.value,
                total_iterations=state.iteration,
                total_errors=len(state.errors),
                critique_scores=state.critique_scores,
                model=settings.model
            )
            return state

        while state.status == AgentStatus.RUNNING and state.iteration < state.max_iterations:
            state.iteration += 1
            logger.info(f"Iteration {state.iteration}/{state.max_iterations}")

            # Apply memory sliding window
            state.history = await self.memory_window.trim(state.history)
            
            history_tokens = self.memory_window.get_total_tokens(state.history)
            metrics.log_event("iteration_start", {
                "iteration": state.iteration,
                "history_tokens_approx": history_tokens
            })

            # Build prompt list for LLM call
            messages_payload = [{"role": msg.role, "content": msg.content} for msg in state.history]

            try:
                # LLM Call
                llm_response = await llm_router.generate(
                    messages_payload,
                    response_schema=LLMDecision,
                    temperature=settings.temperature
                )
                metrics.token_tracker.track_call(llm_response.input_tokens, llm_response.output_tokens)
                logger.info(f"LLM content: {llm_response.content}")

                # Output validation
                decision = OutputFilter.validate_decision(llm_response.content)
                logger.info(f"Parsed decision thought: {decision.thought}")
                metrics.log_event("decision_parsed", {
                    "action": decision.action,
                    "skill_name": decision.skill_name
                })
                
                # Log Thought & Action to history
                state.history.append(Message(
                    role="assistant",
                    content=llm_response.content,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

                # Route Action
                action_result = await self.router.route(decision, state)
                logger.info(f"Action result: {action_result}")

                # Successful execution step, reset consecutive errors
                state.consecutive_errors = 0

                # Append result as observation/tool response
                state.history.append(Message(
                    role="user",
                    content=f"Observation: {action_result}",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

                # Store step in trajectory
                trajectory_steps.append(TrajectoryStep(
                    iteration=state.iteration,
                    thought=decision.thought,
                    action=decision.action,
                    skill_name=decision.skill_name,
                    arguments=decision.arguments,
                    observation=action_result,
                    success=True,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

                # Persist observation to episodic memory
                if settings.episodic_memory_enabled and decision.action == "call_skill":
                    from src.context.memory.memory_store import EpisodicMemoryStore
                    memory_store = EpisodicMemoryStore(db_path=settings.memory_db_path)
                    memory_store.store(
                        session_id=state.session_id,
                        role=state.current_agent,
                        content=f"Task: {task} | Skill '{decision.skill_name}' output: {action_result[:300]}",
                        tags=f"{decision.skill_name},{state.current_agent}"
                    )

                # If the action completed or paused the run
                if state.status == AgentStatus.SUCCESS:
                    state.metadata["proposed_response"] = action_result
                    break
                elif state.status == AgentStatus.WAITING_FOR_HUMAN:
                    break

            except Exception as e:
                metrics.log_event("iteration_error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })

                trajectory_steps.append(TrajectoryStep(
                    iteration=state.iteration,
                    thought=getattr(decision, 'thought', 'N/A') if 'decision' in locals() else 'N/A',
                    action=getattr(decision, 'action', 'error') if 'decision' in locals() else 'error',
                    skill_name=getattr(decision, 'skill_name', None) if 'decision' in locals() else None,
                    arguments=getattr(decision, 'arguments', {}) if 'decision' in locals() else {},
                    observation=f"Error: {str(e)}",
                    success=False,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

                # Auto-correction / self-healing
                await LoopRecovery.recover(e, state)
                if state.status == AgentStatus.FAILED:
                    break

        if state.iteration >= state.max_iterations and state.status == AgentStatus.RUNNING:
            logger.warning("Max iterations reached without success.")
            state.status = AgentStatus.FAILED
            state.errors.append("Max iterations exceeded.")

        # Persist final state to disk
        state_json = state.model_dump_json(indent=2)
        os_path = ".agent/state.json"
        import os
        os.makedirs(".agent", exist_ok=True)
        with open(os_path, "w", encoding="utf-8") as f:
            f.write(state_json)

        # Export Trajectory
        if settings.trajectory_logging_enabled:
            TrajectoryLogger.export(
                session_id=state.session_id,
                task=task,
                steps=trajectory_steps,
                final_status=state.status.value
            )

        # Finalize and persist metrics
        metrics.finalize(
            final_status=state.status.value,
            total_iterations=state.iteration,
            total_errors=len(state.errors),
            critique_scores=state.critique_scores,
            model=settings.model
        )

        return state

