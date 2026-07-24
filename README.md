# Agentic Builder (Python Template Project)

Ce projet est un template moderne et robuste pour implémenter un agent autonome utilisant le pattern **ReAct** (Reasoning and Action) avec Python, conforme aux principes du Master Playbook.

---

## Architecture du Projet

* **`.agent/` (Documentation Opérationnelle / SSOT)** :
  * `AGENT.md`: Identité de l'Orchestrateur, directives et posture.
  * `CONTEXT.md`: Limites du périmètre applicatif et API autorisées.
  * `ARCHITECTURE.md`: Détails sur le workflow et les permissions.
  * `USER.md`: Profilage comportemental de l'utilisateur final.
* **`src/` (Le Harnais)** :
  * `main.py`: Point d'entrée de la boucle d'exécution.
  * `lms/`: Abstraction des providers LLM (Gemini, OpenAI) avec failover déterministe.
  * `context/`: État d'agent (`state.py` typé Pydantic) et fenêtre de mémoire glissante.
  * `harness/`: Guardrails (input/output filters), client MCP générique, et catalogue de compétences (Skills).
  * `loop/`: Boucle de State Machine asynchrone, routeur sécurisé et auto-correction (`recovery.py`).
  * `telemetry/`: Logger structuré au format JSON et compteur de tokens.

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
   GEMINI_API_KEY=votre_cle_api_ici
   ```

---

## Utilisation

Vous pouvez démarrer l'agent directement via la commande CLI :
```bash
python src/main.py "Rechercher des informations sur le protocole MCP"
```

Sans clé API configurée, l'agent s'exécutera automatiquement en **mode simulation/mock** pour valider la logique comportementale et l'enchaînement des étapes de sa boucle.

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
