# Agentic Builder (Python Template Project)

<p align="center">
  🌐 <b>Language:</b>
  <b>English</b> |
  <a href="README.fr.md">Français</a>
</p>

---

**Agentic Builder** is a modern, production-grade **SDK and CLI Scaffold Engine** for building, scaffolding, and patching autonomous AI agents in Python using the **ReAct** (Reasoning + Action) pattern and **Master Playbook** engineering principles.

It enables platform meta-agents (Antigravity, CodeX, Cloud-Code, Hermes) to scaffold new autonomous projects via CLI and patch them incrementally (`--add-skill`, `--add-ui`, `--set-model`).

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
6. **Read-Only `/grill-me` Lock (Phase 0)**: Hard block on modifying/destructive skills until the user approves the impact analysis and scope. Auto-injects approved scoping into the system prompt context.
7. **Telemetry & Trajectory Export**: Token/cost tracking and generic JSONL trajectory exports (`.agent/trajectory_*.jsonl`) for benchmarks and fine-tuning.
8. **Frugality & Determinism**: Free-tier first defaults (`gemini-2.5-flash-lite`), zero heavy dependencies, and 100% automated test coverage.

---

## 🔄 Two-Step Workflow (Context Setup vs Terminal Execution)

To prevent identity confusion between the development assistant (Antigravity meta-agent) and the executed product agent (`agentic-builder`), follow this standard workflow:

```text
┌─────────────────────────────────────────────────────────┐
│ Step 1: Context & Prompt Setup (Chat with Antigravity)  │
│ Configure .agent/ rules, system prompts, skills, .env    │
└───────────────────────────┬─────────────────────────────┘
                            │ (Hand-off to Terminal)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: Task Execution (In your Terminal / Telegram)    │
│ python src/main.py "Your real-world business task"       │
└─────────────────────────────────────────────────────────┘
```

1. **Step 1 — Setup with Antigravity (IDE Chat)**: Use Antigravity to architect your agent, tune `orchestrator_system.md`, configure skills, setup memory, and verify test suites.
2. **Step 2 — Execution in Terminal (Product Hand-off)**: Run your actual task in your local terminal (or via Telegram). Antigravity will automatically remind you of this transition when setup is complete.

---

## Project Structure

* **`.agent/` (Operational Documentation / SSOT)**:
  * `AGENT.md`: Orchestrator identity, mandatory directives, and 2-step workflow rules.
  * `CONTEXT.md`: Scope boundaries and allowed APIs.
  * `ARCHITECTURE.md`: Execution loop details, memory, and Git rules.
  * `USER.md`: End-user behavioral profile and Golden Identity Rule.
* **`src/` (The Harness)**:
  * `main.py`: CLI & Telegram entry point router.
  * `entrypoints/`: Execution entry points (`telegram_bot.py`).
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
   # Mandatory free-tier Google AI Studio API Key (gemini-2.5-flash-lite)
   GEMINI_API_KEY=your_api_key_here

   # Optional Telegram Bot & Render config
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ALLOWED_TELEGRAM_USERS=123456789,@username
   ```

---

## Usage

### ⚡ 1-Click Launcher (Easiest!)
- **Windows**: Double-click **`run.bat`** (or execute `.\run.bat` in your terminal). The launcher prompts you for your task or offers to resume any pending `/grill-me` session automatically!
- **Linux/macOS**: Run `./run.sh` in your terminal.
- **Telegram Bot 1-Click**: Double-click **`bot.bat`**.

---

### 💻 Manual CLI Mode
Run the agent via the manual CLI command:
```bash
python src/main.py "Research information about Model Context Protocol (MCP)"
```
*Without an API key, the agent automatically runs in **simulation/mock mode** to validate loop logic and step transitions.*

### 2. Telegram Bot Mode (Optional)
Run as an interactive Telegram Bot (Long-Polling Async):
```bash
python src/main.py --mode telegram
```

### 3. Optional 24/7 Cloud Deployment (Render)
Deploy as a free 24/7 **Background Worker** on Render.com using the included `render.yaml` Blueprint file.

## 🛠️ SDK CLI Commands (For Meta-Agents & Developers)

Platform meta-agents (Antigravity, CodeX, Cloud-Code, Hermes) call the SDK CLI to scaffold new agents and patch existing projects:

### 1. Scaffold a New Project (`new`)
```bash
python -m src.cli new my_agent --type react --skills researcher,tester --model gemini-2.5-flash-lite --json
```

### 2. Patch an Existing Project (`add`)
```bash
# Add a skill
python -m src.cli add skill git_push --project-dir ../my_agent --json

# Enable UI dashboard
python -m src.cli add ui --project-dir ../my_agent --port 7860 --json

# Change primary/fallback model
python -m src.cli add model gemini-2.5-pro --fallback openai/gpt-4o --project-dir ../my_agent --json
```

### 3. Inspect Project & List Assets (`info`, `list`)
```bash
python -m src.cli info --project-dir ../my_agent --json
python -m src.cli list types --json
```

---

## Creating a New Project from this Template

To instantiate a clean, production-ready project:

- **⚡ 1-Click Mode (Easiest!)**: Double-click **`new_project.bat`** (on Windows) or run `./new_project.sh` (on Linux/macOS). Simply type your new project name when prompted!
- **💻 Manual Mode**:
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
