import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.harness.skills.git_push.skill import GitPushSkill
from src.context.state import AgentState

@pytest.mark.asyncio
async def test_git_push_skill_blocks_main_master(clean_state):
    skill = GitPushSkill()
    res = await skill.execute({"commit_message": "test", "branch_name": "main"}, clean_state)
    assert res.success is False
    assert "Interdiction absolue de pousser directement" in res.error

    res2 = await skill.execute({"commit_message": "test", "branch_name": "master"}, clean_state)
    assert res2.success is False
    assert "Interdiction absolue de pousser directement" in res2.error

@pytest.mark.asyncio
async def test_git_push_skill_blocks_env_leak(clean_state):
    skill = GitPushSkill()
    
    def mock_run(args, **kwargs):
        mock = MagicMock()
        mock.returncode = 0
        if "rev-parse" in args:
            mock.stdout = "true"
        elif "remote" in args:
            mock.stdout = "origin git@github.com:user/repo.git"
        elif "status" in args:
            mock.stdout = " M src/main.py\n?? .env\n"
        return mock

    with patch("subprocess.run", side_effect=mock_run):
        res = await skill.execute({"commit_message": "test", "branch_name": "dev-agent"}, clean_state)
        assert res.success is False
        assert "Le fichier .env a failli être indexé" in res.error

@pytest.mark.asyncio
async def test_git_push_skill_blocks_no_remote(clean_state):
    skill = GitPushSkill()
    
    def mock_run(args, **kwargs):
        mock = MagicMock()
        mock.returncode = 0
        if "rev-parse" in args:
            mock.stdout = "true"
        elif "remote" in args:
            mock.stdout = ""  # No remote origin
        return mock

    with patch("subprocess.run", side_effect=mock_run):
        res = await skill.execute({"commit_message": "test", "branch_name": "dev-agent"}, clean_state)
        assert res.success is False
        assert "Aucun remote 'origin' n'est configuré" in res.error

@pytest.mark.asyncio
async def test_git_push_skill_success(clean_state):
    skill = GitPushSkill()
    
    calls = []
    def mock_run(args, **kwargs):
        calls.append(args)
        mock = MagicMock()
        mock.returncode = 0
        if "rev-parse" in args and "--is-inside-work-tree" in args:
            mock.stdout = "true"
        elif "remote" in args:
            mock.stdout = "origin git@github.com:user/repo.git"
        elif "status" in args:
            mock.stdout = " M src/main.py\n"
        elif "diff" in args:
            mock.returncode = 1  # changes exist
        elif "rev-parse" in args and "HEAD" in args:
            mock.stdout = "mock-sha-123456"
        return mock

    with patch("subprocess.run", side_effect=mock_run):
        res = await skill.execute({"commit_message": "feat: test message", "branch_name": "dev-agent"}, clean_state)
        assert res.success is True
        assert "Commit SHA : mock-sha-123456" in res.output
        
        flat_calls = [c[0] + " " + c[1] for c in calls if len(c) > 1]
        assert any("git checkout" in c for c in flat_calls)
        assert any("git add" in c for c in flat_calls)
        assert any("git commit" in c for c in flat_calls)
        assert any("git push" in c for c in flat_calls)
