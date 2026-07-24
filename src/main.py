import asyncio
import sys
import uuid
import logging
from typing import Optional
from config.settings import settings
from src.context.state import AgentState, AgentStatus
from src.harness.skills.researcher.skill import ResearcherSkill
from src.harness.skills.git_push.skill import GitPushSkill
from src.loop.router import LoopRouter
from src.loop.engine import AgentEngine
from src.loop.task_loop import TaskLoop

# Setup basic logger
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agentic_builder.main")

async def run_agent(task: Optional[str] = None, resume: bool = False):
    logger.info("Initializing Agent System...")
    
    # 1. Initialize Skills catalog
    researcher_skill = ResearcherSkill()
    git_push_skill = GitPushSkill()
    skills_map = {
        researcher_skill.name: researcher_skill,
        git_push_skill.name: git_push_skill
    }
    
    # 2. Setup Loop router, Engine and TaskLoop
    router = LoopRouter(skills=skills_map)
    engine = AgentEngine(router=router)
    task_loop = TaskLoop(engine=engine)
    
    # 3. Setup AgentState: Resume or New
    if resume:
        logger.info("Resuming agent session...")
        try:
            state = AgentState.load_from_file(".agent/state.json")
            state.metadata["grill_me_approved"] = True
        except Exception as e:
            logger.error(f"Failed to resume session: {e}")
            sys.exit(1)
        
        # Deduce task if not specified
        if not task:
            for msg in state.history:
                if msg.role == "user" and not msg.content.startswith("Observation:"):
                    task = msg.content
                    break
            if not task:
                task = "Initialize dynamic agent template"
    else:
        if not task:
            task = "Initialize dynamic agent template"
        state = AgentState(
            session_id=str(uuid.uuid4()),
            injected_skills=list(skills_map.keys())
        )
    
    # 4. Execute Task Loop (Ralph Loop)
    final_state = await task_loop.run(task, state)
    
    logger.info(f"Execution complete. Final Status: {final_state.status}")
    if final_state.status == AgentStatus.SUCCESS:
        print("\n[SUCCESS] Task Completed Successfully!")
    elif final_state.status == AgentStatus.WAITING_FOR_HUMAN:
        print("\n[WARNING] Awaiting Human Input.")
    else:
        print(f"\n[FAILED] Task Failed. Errors: {final_state.errors}")

def main():
    args = sys.argv[1:]

    if "--mode" in args and "telegram" in args:
        from src.entrypoints.telegram_bot import run_telegram_bot
        run_telegram_bot()
        return

    resume = False
    if "--resume" in args:
        resume = True
        args.remove("--resume")
        
    task = args[0] if len(args) > 0 and not args[0].startswith("--") else None
    asyncio.run(run_agent(task, resume=resume))


if __name__ == "__main__":
    main()
