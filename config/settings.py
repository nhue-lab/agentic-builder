import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # Agent configs
    # Default: gemini-2.5-flash-lite — free tier on Google AI Studio (30 RPM, 1M TPM)
    # Switch to gemini-2.5-pro for production when performance matters.
    model: str = "gemini-2.5-flash-lite"
    fallback_model: str = "gemini-2.5-flash"
    critique_model: str = "gemini-2.5-flash-lite"
    critique_threshold: float = 0.7
    temperature: float = 0.2
    max_tokens_per_session: int = 500000
    max_consecutive_iterations: int = 15
    system_prompt_path: str = "src/prompt/templates/orchestrator_system.md"
    sandbox_allowed_roots: list[str] = ["."]
    grill_me_enabled: bool = True
    git_default_branch: str = "dev-agent"

    # Telemetry
    log_level: str = "INFO"
    trajectory_logging_enabled: bool = True

    # Memory & Hermes Features
    episodic_memory_enabled: bool = True
    memory_db_path: str = ".agent/memory.db"
    memory_top_k: int = 3

    # Sub-agent configuration
    subagent_enabled: bool = True
    subagent_allowed_skills: list[str] = ["researcher", "tester"]
    subagent_max_depth: int = 1

    # Read-only skills during Grill-Me phase
    read_only_skills: list[str] = ["researcher", "tester"]

    # Config path
    mcp_config_path: str = "config/mcp_servers.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton settings instance
settings = Settings()
