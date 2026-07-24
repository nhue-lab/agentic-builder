import pytest
import sys
from unittest.mock import patch, MagicMock
from scripts.create_project import github_onboarding

def test_github_onboarding_non_interactive():
    with patch("sys.stdin.isatty", return_value=False), \
         patch("builtins.print") as mock_print:
        github_onboarding("dummy_dir")
        mock_print.assert_any_call("[GitHub Setup] Non-interactive session, skipping.")

def test_github_onboarding_skipped_by_user():
    with patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", return_value="n"), \
         patch("builtins.print") as mock_print:
        github_onboarding("dummy_dir")
        mock_print.assert_any_call("[GitHub Setup] Skipped.")

def test_github_onboarding_git_missing():
    mock_run = MagicMock()
    mock_run.returncode = 127
    
    with patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", return_value="y"), \
         patch("subprocess.run", return_value=mock_run), \
         patch("builtins.print") as mock_print:
        github_onboarding("dummy_dir")
        mock_print.assert_any_call("[GitHub Setup] Warning: git is not installed or not in PATH. Skipping.")

def test_github_onboarding_success():
    inputs = ["y", "https://github.com/user/myproject.git"]
    
    def mock_input(*args, **kwargs):
        return inputs.pop(0)

    calls = []
    def mock_run(args, **kwargs):
        calls.append(args)
        mock = MagicMock()
        mock.returncode = 0
        if "config" in args:
            mock.stdout = "user@example.com\n"
        elif "version" in args:
            mock.stdout = "git version 2.40.0\n"
        return mock

    with patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", side_effect=mock_input), \
         patch("subprocess.run", side_effect=mock_run), \
         patch("builtins.print") as mock_print:
        
        github_onboarding("my_target_dir")
        
        flat_calls = [" ".join(c) for c in calls]
        assert any("git init" in c for c in flat_calls)
        assert any("git remote add origin" in c for c in flat_calls)
        assert any("git add ." in c for c in flat_calls)
        assert any("git commit" in c for c in flat_calls)
        assert any("git push" in c for c in flat_calls)
        mock_print.assert_any_call("[GitHub Setup] Successful connection and push to GitHub.")
