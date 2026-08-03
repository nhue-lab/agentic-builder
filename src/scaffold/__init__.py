"""
Scaffold package for Agentic Builder SDK.
Provides project generation and incremental patching for autonomous agents.
"""
from .generator import ScaffoldGenerator
from .patcher import ProjectPatcher
from .validator import ScaffoldValidator

__all__ = ["ScaffoldGenerator", "ProjectPatcher", "ScaffoldValidator"]
