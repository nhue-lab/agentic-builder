import os
import pytest
from pathlib import Path
from src.harness.guardrails.path_sandbox import PathSandbox

def test_path_sandbox_default_root():
    sandbox = PathSandbox()
    # By default, allowed roots should contain the resolved path of "."
    expected_root = Path(".").resolve()
    assert expected_root in sandbox.allowed_roots

def test_path_sandbox_custom_roots(tmp_path):
    root1 = tmp_path / "sandbox1"
    root2 = tmp_path / "sandbox2"
    root1.mkdir()
    root2.mkdir()
    
    sandbox = PathSandbox(allowed_roots=[str(root1), str(root2)])
    assert root1.resolve() in sandbox.allowed_roots
    assert root2.resolve() in sandbox.allowed_roots

def test_path_sandbox_resolve_safe_path_success(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    sandbox = PathSandbox(allowed_roots=[str(root)])
    
    # Accessing a file directly inside root
    safe_file = root / "test.txt"
    safe_file.touch()
    
    resolved = sandbox.resolve_safe_path(str(safe_file))
    assert resolved == safe_file.resolve()
    
    # Accessing a nested file
    nested_dir = root / "nested" / "deep"
    nested_dir.mkdir(parents=True)
    nested_file = nested_dir / "deep_test.txt"
    nested_file.touch()
    
    resolved_nested = sandbox.resolve_safe_path(str(nested_file))
    assert resolved_nested == nested_file.resolve()

def test_path_sandbox_resolve_safe_path_traversal_denied(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    sandbox = PathSandbox(allowed_roots=[str(root)])
    
    # Try to traverse out of root using '..'
    unsafe_path = root / ".." / "outside.txt"
    
    with pytest.raises(PermissionError) as exc_info:
        sandbox.resolve_safe_path(str(unsafe_path))
    assert "outside the allowed sandbox roots" in str(exc_info.value)

def test_path_sandbox_resolve_safe_path_absolute_outside_denied(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    sandbox = PathSandbox(allowed_roots=[str(root)])
    
    # Try to access a path completely outside, like temp directory itself
    outside_path = tmp_path / "outside.txt"
    outside_path.touch()
    
    with pytest.raises(PermissionError) as exc_info:
        sandbox.resolve_safe_path(str(outside_path))
    assert "outside the allowed sandbox roots" in str(exc_info.value)

def test_path_sandbox_symlink_attack_denied(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    sandbox = PathSandbox(allowed_roots=[str(root)])
    
    # File outside the sandbox
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("my secret credentials")
    
    # Symlink inside the sandbox pointing to the file outside
    symlink_file = root / "link_to_secret.txt"
    
    try:
        os.symlink(secret_file, symlink_file)
    except OSError:
        # Symlink creation might fail on Windows if developer mode/admin rights are lacking.
        # If so, skip the symlink resolution check.
        pytest.skip("Symlinks cannot be created (insufficient privileges or unsupported on OS)")
        
    # Checking resolved path security
    with pytest.raises(PermissionError) as exc_info:
        sandbox.resolve_safe_path(str(symlink_file))
    assert "outside the allowed sandbox roots" in str(exc_info.value)
