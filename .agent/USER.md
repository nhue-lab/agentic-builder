- Communication: Concise, markdown formatted.
- Technical background: Advanced.
- Preference: Self-contained files, robust type validations, clean code.

## 🌟 RÈGLE D'OR D'IDENTITÉ & WORKFLOW EN 2 ÉTAPES

1. **Étape 1 — Paramétrage avec Antigravity (dans le Chat IDE)** :
   - L'utilisateur utilise **Antigravity** pour configurer, cadrer et importer un maximum de contexte (`.agent/`, System Prompt, skills, guardrails, `.env`, mémoire).
   - Antigravity s'assure que l'agent est 100% prêt, testé et documenté.

2. **Étape 2 — Exécution dans le Terminal (Passage de relais)** :
   - Dès que le paramétrage est terminé, **l'utilisateur exécute son action réelle directement dans le Terminal** (ou Telegram).
   - Antigravity prévient systématiquement l'utilisateur en lui fournissant la commande exacte à copier-coller dans son terminal pour lancer son agent.

- **Comportement obligatoire** : Si l'utilisateur tente de faire exécuter la tâche métier dans le chat Antigravity, Antigravity lui rappelle ce workflow en 2 étapes et lui indique la commande terminal exacte (`python src/main.py "votre tâche"`).
