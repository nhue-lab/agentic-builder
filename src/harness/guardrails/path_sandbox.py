import os
from pathlib import Path
import logging

logger = logging.getLogger("agentic_builder.guardrails.path_sandbox")

class PathSandbox:
    """Sandbox for restricting filesystem access to allowed root directories."""

    def __init__(self, allowed_roots: list[str] = None):
        """Initialize the sandbox with a list of allowed root directories.
        
        Args:
            allowed_roots: List of directory paths that are allowed.
                           Defaults to ["."] (current directory).
        """
        if allowed_roots is None:
            allowed_roots = ["."]

        self.allowed_roots: list[Path] = []
        for root in allowed_roots:
            try:
                # Resolve the root to its absolute canonical path
                resolved_root = Path(root).resolve()
                self.allowed_roots.append(resolved_root)
            except Exception as e:
                logger.warning(f"Could not resolve allowed root path '{root}': {e}")
                # Fallback to absolute path if resolution fails (e.g. non-existent yet)
                self.allowed_roots.append(Path(root).absolute())

    def resolve_safe_path(self, user_path: str) -> Path:
        """Resolve a user-provided path and verify that it lies within the allowed root directories.
        
        This checks both the resolved (physical) path and the nominal absolute path to prevent
        path traversal (using '..') and symlink attacks pointing outside the allowed roots.

        Args:
            user_path: The file path to validate.

        Returns:
            The resolved absolute Path object.

        Raises:
            PermissionError: If the path is outside the allowed root directories.
        """
        try:
            # 1. Resolve path to eliminate relative segments (..) and symlinks
            resolved_path = Path(user_path).resolve()
        except Exception as e:
            raise PermissionError(f"Access denied: path resolution failed for '{user_path}'. Error: {e}")

        # 2. Get the nominal absolute and normalized path (without resolving symlinks)
        try:
            norm_path = Path(os.path.abspath(user_path))
        except Exception as e:
            raise PermissionError(f"Access denied: invalid path structure for '{user_path}'. Error: {e}")

        # Check if resolved path is within any allowed roots
        in_resolved_sandbox = False
        for root in self.allowed_roots:
            try:
                if resolved_path.is_relative_to(root):
                    in_resolved_sandbox = True
                    break
            except AttributeError:
                # Fallback for Python < 3.9 (just in case)
                try:
                    resolved_path.relative_to(root)
                    in_resolved_sandbox = True
                    break
                except ValueError:
                    continue

        if not in_resolved_sandbox:
            raise PermissionError(
                f"Access denied: resolved path '{resolved_path}' is outside the allowed sandbox roots: "
                f"{[str(r) for r in self.allowed_roots]}"
            )

        # Check if nominal path is within any allowed roots (prevents external symlinks to internal targets)
        in_nominal_sandbox = False
        for root in self.allowed_roots:
            try:
                if norm_path.is_relative_to(root):
                    in_nominal_sandbox = True
                    break
            except AttributeError:
                try:
                    norm_path.relative_to(root)
                    in_nominal_sandbox = True
                    break
                except ValueError:
                    continue

        if not in_nominal_sandbox:
            raise PermissionError(
                f"Access denied: nominal path '{norm_path}' is outside the allowed sandbox roots: "
                f"{[str(r) for r in self.allowed_roots]}"
            )

        return resolved_path
