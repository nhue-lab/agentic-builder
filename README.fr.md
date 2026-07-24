# Agentic Builder (Python Template Project)

<p align="center">
  🌐 <b>Langue :</b>
  <b>Français</b> |
  <a href="README.md">English</a>
</p>

---

**Agentic Builder** est un template moderne et robuste pour implémenter des agents IA autonomes en Python utilisant le pattern **ReAct** (Reasoning + Action) et les principes d'ingénierie du **Master Playbook**.

---

## 📖 Qu'est-ce que le Master Playbook ?

Le **Master Playbook** est un ensemble de 8 piliers de génie logiciel pour concevoir des agents IA autonomes de niveau production, fiables, sécurisés et frugaux :

1. **Source Unique de Vérité (`.agent/`)** : Documentation opérationnelle explicite (`AGENT.md`, `ARCHITECTURE.md`, `USER.md`) cadrant la posture, les limites et l'identité de l'agent.
2. **Priorité au Harnais (`src/`)** : Mettre l'accent sur la robustesse du système hôte (contrats typés Pydantic, routeur avec failover, filtres de sécurité, isolation de bac à sable) plutôt que de compter uniquement sur la mémoire brute du LLM.
3. **Double Boucle d'Exécution (ReAct + Ralph Loop)** :
   * *Boucle Tactique* : Exécution d'outils et de compétences ReAct (`AgentEngine`).
   * *Boucle Stratégique (Ralph Loop)* : Validation indépendante du résultat par un `CritiqueAgent`. En cas d'échec, le contexte est réinitialisé avec réinjection de post-mortem pour éviter la dérive (*context rot*).
4. **Mémoire Épisodique Persistante (FTS5 SQLite)** : Conservation des leçons et des souvenirs clés entre les sessions, stockés localement dans `.agent/memory.db`.
5. **Délégation Sub-Agent Sécurisée** : Sous-agents autonomes isolés avec compétences restreintes et verrou physique de récursion (`max_depth = 1`).
6. **Verrou Read-Only `/grill-me` (Phase 0)** : Blocage strict des compétences modifiantes/destructrices tant que la phase de cadrage d'impact et de risques n'a pas été validée par l'utilisateur. Injection automatique du cadrage approuvé dans le prompt système.
7. **Télémétrie & Export de Trajectoires** : Suivi des tokens/coûts et export systématique des trajectoires au format JSONL générique (`.agent/trajectory_*.jsonl`).
8. **Frugalité & Déterminisme** : Utilisation recommandée du tier gratuit (`gemini-2.5-flash-lite`), zéro dépendance lourde, et 100% de couverture de tests automatisés.

---

## 🔄 Workflow en 2 Étapes (Paramétrage vs Exécution Terminal)

Pour éviter toute confusion entre l'assistant de développement (le méta-agent Antigravity) et l'agent produit exécutable (`agentic-builder`), suivez le workflow standard :

```text
┌─────────────────────────────────────────────────────────┐
│ Étape 1 : Paramétrage & Contexte (Chat avec Antigravity)│
│ Configurer .agent/, system prompt, skills, .env         │
└───────────────────────────┬─────────────────────────────┘
                            │ (Passage de relais au Terminal)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 2 : Exécution Tâche (Dans votre Terminal / Telegram)│
│ python src/main.py "Votre tâche métier réelle"          │
└─────────────────────────────────────────────────────────┘
```

1. **Étape 1 — Paramétrage avec Antigravity (Chat IDE)** : Utilisez Antigravity pour concevoir votre agent, affiner `orchestrator_system.md`, injecter les compétences, configurer la mémoire et valider les tests.
2. **Étape 2 — Exécution dans le Terminal (Passage de relais au Produit)** : Lancez l'action réelle directement dans votre terminal (ou via Telegram). Antigravity vous rappellera automatiquement cette étape une fois le paramétrage terminé.

---

## Architecture du Projet

* **`.agent/` (Documentation Opérationnelle / SSOT)** :
  * `AGENT.md`: Identité de l'Orchestrateur, directives obligatoires et règles de workflow.
  * `CONTEXT.md`: Limites du périmètre applicatif et API autorisées.
  * `ARCHITECTURE.md`: Détails sur les boucles d'exécution, la mémoire et les règles Git.
  * `USER.md`: Profilage comportemental et Règle d'Or d'Identité.
* **`src/` (Le Harnais)** :
  * `main.py`: Point d'entrée CLI et sélecteur de mode.
  * `entrypoints/`: Adaptateurs d'exécution (`telegram_bot.py`).
  * `lms/`: Abstraction des providers LLM (Gemini, OpenAI) avec failover déterministe.
  * `context/`: État d'agent (`state.py` typé Pydantic), fenêtre glissante, et mémoire épisodique SQLite FTS5 (`memory_store.py`).
  * `harness/`: Guardrails (input/output filters, `PathSandbox`, `GrillMeGuard`), client MCP générique, et catalogue de compétences (`Skills`, `SubAgentSkill`).
  * `loop/`: Boucle de State Machine asynchrone, routeur sécurisé avec verrou Read-Only (`router.py`) et auto-correction (`recovery.py`).
  * `telemetry/`: Logger structuré JSON, compteur de tokens/coûts, et exporteur de trajectoires JSONL (`trajectory.py`).

---

## Configuration & Installation

1. **Installer le projet en mode éditable** :
   ```bash
   pip install -e .
   ```
2. **Pour les dépendances de développement (tests)** :
   ```bash
   pip install -e ".[dev]"
   ```
3. **Configurer les variables d'environnement** :
   Créez un fichier `.env` à la racine (s'inspirer de `.env.example`) :
   ```env
   # Clé API Google AI Studio obligatoire (tier gratuit gemini-2.5-flash-lite)
   GEMINI_API_KEY=votre_cle_api_ici

   # Configuration Bot Telegram & Render optionnels
   TELEGRAM_BOT_TOKEN=votre_token_bot_ici
   ALLOWED_TELEGRAM_USERS=123456789,@username
   ```

---

## Utilisation

### ⚡ Mode 1-Clic (Le plus simple !)
- **Windows** : Double-cliquez simplement sur **`run.bat`** (ou lancez `.\run.bat` dans votre terminal). Le script vous demandera votre tâche, ou vous proposera de reprendre une session `/grill-me` en cours !
- **Linux/macOS** : Lancez simplement `./run.sh` dans votre terminal.
- **Bot Telegram 1-Clic** : Double-cliquez sur **`bot.bat`**.

---

### 💻 Mode CLI Manuel
Vous pouvez aussi démarrer l'agent directement via la commande CLI :
```bash
python src/main.py "Rechercher des informations sur le protocole MCP"
```
*Sans clé API configurée, l'agent s'exécutera automatiquement en **mode simulation/mock**.*

### 2. Mode Bot Telegram (Optionnel)
Exécuter sous forme de Bot Telegram interactif (Async Long-Polling) :
```bash
python src/main.py --mode telegram
```

### 3. Déploiement Cloud 24/7 Optionnel (Render)
Déployer en tant que **Background Worker** gratuit 24/7 sur Render.com via le fichier Blueprint `render.yaml`.

---

## Création d'un nouveau projet depuis ce template

Pour instancier un projet autonome propre et prêt à la production :
```bash
python scripts/create_project.py ../mon-nouveau-projet
```
*Le script se chargera de cloner les structures nécessaires, de réinitialiser l'état local et de configurer l'environnement virtuel (`.venv`) dédié.*

---

## Tests

Pour exécuter la suite complète de tests unitaires, d'intégration et de conformité structurelle :
```bash
pytest tests/ -v
```
