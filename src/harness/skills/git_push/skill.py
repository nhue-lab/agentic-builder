import subprocess
import logging
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.context.state import AgentState
from config.settings import settings

logger = logging.getLogger("agentic_builder.skills.git_push")

class GitPushSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "git_push"

    @property
    def description(self) -> str:
        return (
            "Commits and pushes the current code changes to a secure remote branch. "
            "Arguments: {'commit_message': 'string', 'branch_name': 'string' (optional)}"
        )

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        commit_message = arguments.get("commit_message", "")
        if not commit_message:
            return SkillResult(success=False, output="", error="Missing 'commit_message' argument.")

        branch_name = arguments.get("branch_name", settings.git_default_branch)

        # Guardrail: Check that branch name is not main or master
        if branch_name.strip().lower() in ("main", "master"):
            return SkillResult(
                success=False,
                output="",
                error="Alerte Sécurité : Interdiction absolue de pousser directement sur la branche principale (main/master)."
            )

        logger.info(f"Executing git_push skill on branch '{branch_name}' with message: '{commit_message}'")

        try:
            # 1. Check if git repository is initialized
            res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
            if res.returncode != 0:
                return SkillResult(success=False, output="", error="Not a git repository.")

            # 2. Check for remote origin
            remote_res = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
            if "origin" not in remote_res.stdout:
                return SkillResult(
                    success=False,
                    output="",
                    error="Aucun remote 'origin' n'est configuré pour ce dépôt Git. Push annulé."
                )

            # 3. Guardrail: Check that .env is not staged or tracked in Git status
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if ".env" in status.stdout:
                return SkillResult(
                    success=False,
                    output="",
                    error="Alerte Sécurité : Le fichier .env a failli être indexé ou poussé ! Opération annulée."
                )

            # 4. Git checkout -B <branch_name>
            subprocess.run(["git", "checkout", "-B", branch_name], check=True, capture_output=True)

            # 5. Git add .
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # 6. Check if there are changes to commit
            diff_res = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if diff_res.returncode == 0:
                logger.info("No new changes to commit, attempting to push existing commits.")
            else:
                # Git commit -m <commit_message>
                subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)

            # 7. Git push origin <branch_name>
            push_res = subprocess.run(["git", "push", "origin", branch_name], capture_output=True, text=True)
            if push_res.returncode != 0:
                return SkillResult(
                    success=False,
                    output="",
                    error=f"Échec du push vers origin : {push_res.stderr.strip()}"
                )

            # Get the last commit SHA
            sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
            commit_sha = sha_res.stdout.strip()

            return SkillResult(
                success=True,
                output=f"Succès : Code poussé sur la branche '{branch_name}'. Commit SHA : {commit_sha}."
            )

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else str(e)
            return SkillResult(
                success=False,
                output="",
                error=f"Erreur de commande Git : {error_output}"
            )
        except Exception as e:
            return SkillResult(success=False, output="", error=f"Erreur inattendue lors du push : {str(e)}")
