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

---

## 🔮 Jalon 3 — Evolutions Futures (Roadmap À Venir)

- [ ] **Sandboxing Docker de Code Arbitraire** : Intégrer un wrapper Docker léger pour exécuter des scripts Python/Bash générés dynamiquement par l'agent dans une micro-VM étanche.
- [ ] **Communication Directe Inter-Agents (Swarm Protocol)** : Étendre le système de sub-agents pour permettre un canal de communication bidirectionnel synchrone entre agents pairs.
- [ ] **Dashboard de Visualisation des Trajectoires** : Petit outil CLI / web local pour visualiser et rejouer les fichiers `.jsonl` de trajectoire.
- [ ] **Auto-Correction de Code par AST/Linter** : Ajouter un pass d'analyse statique automatique avant la phase de critique.
