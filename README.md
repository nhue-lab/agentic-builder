# Agentic Builder (Python Template Project)

<p align="center">
  🌐 <b>Language:</b>
  <b>English</b> |
  <a href="README.fr.md">Français</a>
</p>

---

**Agentic Builder** is a modern, production-grade template for building autonomous AI agents in Python using the **ReAct** (Reasoning + Action) pattern and the **Master Playbook** engineering principles.

---

## 📖 What is the Master Playbook?

The **Master Playbook** is a set of 8 software engineering pillars designed to build reliable, secure, frugal, and production-ready autonomous AI agents:

1. **Single Source of Truth (`.agent/`)**: Operational documentation (`AGENT.md`, `ARCHITECTURE.md`, `USER.md`) strictly defining the agent's identity, constraints, and operational bounds.
2. **Harness First (`src/`)**: Prioritizing host-system engineering (Pydantic state schemas, failover router, path sandboxing, output guardrails) over raw model intelligence.
3. **Dual-Loop Execution (ReAct + Ralph Loop)**:
   * *Tactical Loop*: ReAct tool execution and skill routing (`AgentEngine`).
   * *Strategic Loop (Ralph Loop)*: Independent solution evaluation by a `CritiqueAgent`. On failure, message context is reset with post-mortem feedback to prevent *context rot*.
4. **Episodic Long-Term Memory (FTS5 SQLite)**: Inter-session memory store retaining lessons and key observations locally in `.agent/memory.db`.
5. **Restricted Sub-Agent Delegation**: Isolated child agents with narrow skill whitelists and a physical recursion lock (`max_depth = 1`).
6. **Read-Only `/grill-me` Lock (Phase 0)**: Hard block on modifying/destructive skills until the user approves the impact analysis and scope.
7. **Telemetry & Trajectory Export**: Token/cost tracking and generic JSONL trajectory exports (`.agent/trajectory_*.jsonl`) for benchmarks and fine-tuning.
8. **Frugality & Determinism**: Free-tier first defaults (`gemini-2.5-flash-lite`), zero heavy dependencies, and 100% automated test coverage.

---

## Project Structure

* **`.agent/` (Operational Documentation / SSOT)**:
  * `AGENT.md`: Orchestrator identity, mandatory directives, and posture.
  * `CONTEXT.md`: Scope boundaries and allowed APIs.
  * `ARCHITECTURE.md`: Execution loop details, memory, and Git rules.
  * `USER.md`: End-user behavioral profile.
* **`src/` (The Harness)**:
  * `main.py`: CLI entry point for the execution loop.
  * `lms/`: LLM provider abstraction (Gemini, OpenAI) with deterministic failover.
  * `context/`: Pydantic agent state (`state.py`), sliding window, and episodic FTS5 memory (`memory_store.py`).
  * `harness/`: Guardrails (input/output filters, `PathSandbox`, `GrillMeGuard`), generic MCP client, and skill catalog (`SubAgentSkill`).
  * `loop/`: Async state machine, router with Read-Only lock (`router.py`), and self-healing (`recovery.py`).
  * `telemetry/`: Structured JSON logger, token/cost tracker, and JSONL trajectory exporter (`trajectory.py`).

---

## Setup & Installation

1. **Install the package in editable mode**:
   ```bash
   pip install -e .
   ```
2. **Install development dependencies (tests)**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Configure Environment Variables**:
   Create a `.env` file at the root (see `.env.example`):
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

---

## Usage

Run the agent via the CLI:
```bash
python src/main.py "Research information about Model Context Protocol (MCP)"
```

*Without an API key, the agent automatically runs in **simulation/mock mode** to validate loop logic and step transitions.*

---

## Creating a New Project from this Template

To instantiate a clean, production-ready project:
```bash
python scripts/create_project.py ../my-new-project
```
*The script clones the structure, resets local state, and configures a dedicated virtual environment (`.venv`).*

---

## Testing

To run the complete test suite (unit, integration, and compliance):
```bash
pytest tests/ -v
```
