# Roadmap & Journal des Décisions Structurantes — Agentic Builder

> **📌 RÈGLE DE GOUVERNANCE DU PROJET (OBLIGATOIRE)** :
> Ce fichier `ROADMAP.md` doit **impérativement être mis à jour** dès qu'un choix d'architecture, de sécurité, de modèle ou de gouvernance important est arrêté lors des discussions avec l'utilisateur.

---

## 📅 Dernier état mis à jour : 24 Juillet 2026

---

## 🎯 Vision & Objectif Globaux
Fournir le template Python le plus propre, modulaire, sécurisé et frugal pour construire des agents autonomes ReAct de niveau production, agnostiques au fournisseur tout en profitant des meilleures capacités d'agents modernes (mémoire épisodique, sub-agents, trajectoires, guardrails stricts).

---

## 🚀 Jalons & Historique des Décisions

### 🟢 Jalon 1 — Harnais ReAct de Base & Quality Assurance (Validé)
- [x] Boucle ReAct asynchrone avec State Machine typée Pydantic (`src/context/state.py`, `src/loop/engine.py`).
- [x] Invalidation de contexte par validation croisée (`TaskLoop` / Ralph Loop + `CritiqueAgent`).
- [x] Isolation du système de fichiers avec `PathSandbox` (prévention du directory traversal & attaques par symlinks).
- [x] Failover déterministe entre providers LLM (`llm_router`).
- [x] Télémétrie JSON et suivi précis des tokens/coûts.

---

### 🟢 Jalon 2 — Upgrades Hermes Agent & Verrous de Sécurité (Validé le 24 Juillet 2026)

#### 1. Mémoire Épisodique Persistante (`src/context/memory/memory_store.py`)
- **Décision (24/07/2026)** : SQLite FTS5 strictement **local au projet** (`.agent/memory.db`).
- **Motif** : Aucune dépendance externe (stdlib Python), rappel BM25 rapide (< 5ms), isolation totale entre projets.

#### 2. Sub-Agent Spawning (`src/harness/skills/subagent/subagent_skill.py`)
- **Décision (24/07/2026)** : Délégation à des sous-agents isolés avec **privilèges et compétences restreints** (`subagent_allowed_skills`).
- **Motif** : Préserver le budget de tokens de l'agent principal. Garde-fou physique `max_depth = 1` imposé pour prévenir toute récursion infinie.

#### 3. Trajectory Logger (`src/telemetry/trajectory.py`)
- **Décision (24/07/2026)** : Export automatique des sessions vers un format **JSONL générique** (`.agent/trajectory_<session_id>.jsonl`).
- **Motif** : Permettre l'évaluation ultérieure (benchmarks, fine-tuning, DPO) sans s'enfermer dans un framework propriétaire.

#### 4. Verrouillage Read-Only Obligatoire pendant `/grill-me` (`src/loop/router.py`)
- **Décision (24/07/2026)** : Verrouillage strict en **lecture seule** tant que la phase de cadrage d'impact `/grill-me` n'a pas été formellement approuvée par l'utilisateur (`GRILL_ME_APPROVED`).
- **Motif** : Garantir qu'aucune modification ni action destructrice ne peut avoir lieu avant validation explicite des leviers et risques du projet.

#### 6. Adaptateur Telegram & Déploiement Cloud 24/7 Render (`src/entrypoints/telegram_bot.py`, `render.yaml`)
- **Décision (24/07/2026)** : Intégration d'un adaptateur Telegram Async Long-Polling (`httpx` natif) avec whitelist de sécurité (`ALLOWED_TELEGRAM_USERS`), couplé à un Blueprint `render.yaml` pour un déploiement gratuit 24/7 en tant que **Background Worker**.
- **Motif** : Permettre de contrôler l'agent à tout moment via Telegram (même PC éteint), avec réponse instantanée (< 1s), suivi du statut `/status` et validation interactive `/approve` de la phase `/grill-me`.

#### 7. Caractère Optionnel et Conditionnel du Déploiement Cloud 24/7
- **Décision (24/07/2026)** : Le déploiement cloud (Render / Telegram bot 24/7) est **strictement optionnel**. Si l'hébergement cloud n'est pas pertinent pour les objectifs d'un projet dérivé (ex: CLI local, script batch), il ne doit pas être imposé ni activé. L'agent fonctionne par défaut de façon autonome en CLI local.

#### 8. Règle Cardinale d'Ingénierie — Déterminisme, Frugalité, Sécurité et Robustesse
- **Décision (24/07/2026)** : Pour toute contrainte ou exigence demandée par l'utilisateur, Antigravity (le méta-agent) et l'agent produit (`agentic-builder`) doivent impérativement viser la solution la plus **déterministe, frugale, sécurisée et robuste** possible.
- **Motif** : Éliminer la sur-ingénierie et les dépendances lourdes injustifiées au profit de garanties logicielles strictes (Pydantic, verrous physiques, tests 100% automatisés).

#### 9. Lanceurs 1-Clic Cross-Platform (`run.bat`, `run.sh`, `bot.bat`)
- **Décision (24/07/2026)** : Ajout de scripts d'exécution 1-clic pour Windows (`run.bat`, `bot.bat`) et Linux/macOS (`run.sh`).
- **Motif** : Éliminer toute complexité d'exécution : double-clic pour lancer l'agent, saisir sa tâche ou reprendre une session `/grill-me` sans retenir de commandes CLI.

#### 10. Raccourcis de Création de Projet 1-Clic (`new_project.bat`, `new_project.sh`)
- **Décision (24/07/2026)** : Ajout des scripts `new_project.bat` (Windows) et `new_project.sh` (Linux/macOS) à la racine.
- **Motif** : Permettre d'instancier un nouveau projet propre d'un simple double-clic ou saisie du nom, sans retenir la syntaxe Python.

---

### 🟢 Jalon 2.5 — Couche UI Locale (Dashboard Temps Réel) (02 Août 2026)

#### 11. UISkill — Composant Infra Observer (non-callable par le LLM)
- **Décision (02/08/2026)** : La UISkill est un composant infra injecté directement dans `AgentEngine` (pattern Observer), **pas un skill LLM-callable**. L'engine appelle `await self.ui_skill.emit_event(...)` après chaque étape ReAct.
- **Motif** : Séparation stricte des responsabilités — le LLM ne doit pas pouvoir déclencher l'UI lui-même.

#### 12. Stack Technique UI — FastAPI SSE + Vanilla JS
- **Décision (02/08/2026)** : FastAPI async intégré au process via un thread daemon, SSE (Server-Sent Events) pour le push temps réel, dashboard Vanilla JS + CSS pur (glassmorphism dark, palette HSL purple/cyan, Inter + JetBrains Mono).
- **Motif** : Zéro dépendance JS côté client, SSE natif HTTP (pas de WebSocket overhead), graceful degradation si FastAPI absent.

#### 13. Règle d'Agnosticisme Partiel du Harness (Insight Critique)
- **Décision (02/08/2026)** : Le harness est agnostique sur la couche **System & Safety** (sandbox, guardrails, PermissionError) mais doit s'adapter aux spécificités de chaque famille de modèles sur 3 points :
  1. **Parsing Tool Calling** : chaque provider a son format natif (XML/JSON Anthropic, JSON Schema OpenAI, balises texte DeepSeek).
  2. **Context Engineering** : injection du system prompt et des règles selon les biais d'attention du modèle.
  3. **Reasoning Tokens** : isolation des blocs `<think>...</think>` (DeepSeek-R1, Claude Thinking, o1/o3) avant parsing du `LLMDecision`.
- **Implémentation** : `_extract_reasoning_tokens()` dans `engine.py`, event `REASONING_TOKEN` dans `UIEvent`, panneau dédié dans le dashboard.

#### 14. Model-Awareness du LLMRouter
- **Décision (02/08/2026)** : Le singleton `llm_router` expose `last_used_provider` et `last_used_model` après chaque `generate()`. L'engine lit ces attributs pour enrichir les UIEvents sans coupler UISkill au router.
- **Motif** : Le dashboard affiche en temps réel si l'agent utilise le provider primaire (Gemini) ou le fallback (OpenAI).

#### 15. Frugalité UI — Off by Default + Graceful Degradation
- **Décision (02/08/2026)** : `ui_enabled: false` dans `agent_config.json`. Activation via `--ui` flag CLI ou `.env`. Si FastAPI/uvicorn manquent : log warning, pas d'exception, agent continue normalement.

---

---

### 🟢 Jalon 3 — SDK Scaffold & Moteur de Patching Incrémental (02 Août 2026)

#### 16. Agentic Builder comme SDK CLI pour Méta-Agents
- **Décision (02/08/2026)** : `agentic-builder` devient un SDK de scaffold CLI appelé par les méta-agents des plateformes agentiques (Antigravity, CodeX, Cloud-Code, Hermes).
- **Motif** : La phase de cadrage (`/grill-me`) s'effectue dans la plateforme hôte. `agentic-builder` intervient en moteur déterministe pour scaffolder ou patcher un agent sans faire de chat redondant.

#### 17. Architecture CLI — `new`, `add`, `list`, `info`
- **`new`** : Génère un projet d'agent autonome avec `pyproject.toml`, `_meta.json`, `config/`, `src/`, `tests/` et launchers `run.bat`/`run.sh`.
- **`add`** : Effectue un patch incrémental sur un projet existant (`add skill <name>`, `add ui [--port 7860]`, `add model <name>`).
- **`list` & `info`** : Expose les types et skills disponibles, ainsi que les métadonnées d'un projet pour le parsing JSON du méta-agent.

#### 18. Règle "Terminal First"
- **Décision (02/08/2026)** : Tout projet scaffoldé commence **toujours par le terminal** (`ui_enabled: false`). L'UI n'est ajoutée qu'ultérieurement via `agentic-builder add ui` si l'usage le confirme.

---

## 🔮 Jalon 4 — Evolutions Futures (Roadmap À Venir)

- [ ] **Sandboxing Docker de Code Arbitraire** : Intégrer un wrapper Docker léger pour exécuter des scripts Python/Bash générés dynamiquement par l'agent dans une micro-VM étanche.
- [ ] **Communication Directe Inter-Agents (Swarm Protocol)** : Étendre le système de sub-agents pour permettre un canal de communication bidirectionnel synchrone entre agents pairs.
- [x] **Dashboard de Visualisation des Trajectoires** : ~~Petit outil CLI / web local pour visualiser et rejouer les fichiers `.jsonl` de trajectoire.~~ → Couvert par Jalon 2.5 (UISkill + SSE dashboard).
- [ ] **Auto-Correction de Code par AST/Linter** : Ajouter un pass d'analyse statique automatique avant la phase de critique.
- [ ] **Adapters Thinking Models** : Étendre `_extract_reasoning_tokens()` pour gérer les formats propriétaires de chaque provider (Anthropic `thinking` blocks JSON, o1/o3 `reasoning_content`, etc.).
