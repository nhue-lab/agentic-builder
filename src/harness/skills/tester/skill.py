import logging
import asyncio
import sys
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.context.state import AgentState

logger = logging.getLogger("agentic_builder.skills.tester")

class TesterSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "tester"

    @property
    def description(self) -> str:
        return "Executes pytest on the workspace to verify code correctness. Arguments: {'test_path': 'optional specific test file or directory path, e.g. tests/unit/test_state.py'}"

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        test_path = arguments.get("test_path", "tests/")
        logger.info(f"Executing TesterSkill with path: {test_path}")

        # Construct the command: python -m pytest <test_path>
        cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")
            
            success = (process.returncode == 0)
            
            combined_output = output
            if error_output:
                combined_output += f"\n--- Standard Error ---\n{error_output}"
                
            if success:
                logger.info("Tests executed successfully.")
                return SkillResult(success=True, output=combined_output)
            else:
                logger.warning(f"Tests failed with return code {process.returncode}.")
                return SkillResult(
                    success=False, 
                    output=combined_output, 
                    error=f"Tests failed (code {process.returncode}). Check output for details."
                )
                
        except Exception as e:
            logger.exception("Failed to execute tests.")
            return SkillResult(success=False, output="", error=f"Execution error: {str(e)}")
