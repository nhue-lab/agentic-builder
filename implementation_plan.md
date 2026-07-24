# Implementation Plan: Phase 4 - Resilient Retry with Tenacity

## Phase 0: Conception Architecturale (Design Doc)

### 1. Architecture des composants
L'implémentation se fait au sein du composant de routage LLM (`src/lms/router.py`).
Le routeur délègue actuellement les appels en premier lieu à `primary_client` (GeminiClient) et en cas d'erreur bascule directement sur `fallback_client` (OpenAIClient).
Nous introduisons un mécanisme de retry automatique et résilient sur le `primary_client` pour intercepter les erreurs transitoires du réseau ou de l'API (quota/rate-limit, timeouts, 5xx) avant de basculer vers le fallback.

### 2. Contrats de données (Interfaces)
- Entrée : La méthode `LLMRouter.generate` accepte des requêtes standard via `messages`, `response_schema` et `**kwargs`.
- Sortie : Elle renvoie un `LLMResponse` ou lève une exception si le fallback échoue également.
- Comportement de retry :
  - Nombre maximum de tentatives : 3
  - Backoff exponentiel : Départ à 2s, max à 10s.
  - Filtre : Uniquement sur les exceptions identifiées comme transitoires (HTTP 429, 5xx, timeouts de httpx ou du SDK).

### 3. Gestion de l'état (State Management)
L'état de retry est géré en mémoire par le moteur de retry asynchrone de `tenacity`.
Les compteurs et délais ne sont pas persistés inter-sessions car il s'agit d'une résilience immédiate en cours de requête.

### 4. Arborescence cible
Les fichiers impactés sont :
- `pyproject.toml` (Ajout de la dépendance `tenacity>=8.2.0`)
- `src/lms/router.py` (Intégration de `AsyncRetrying` de `tenacity`)
- `tests/unit/test_router.py` (Création de tests unitaires pour le retry et le fallback)

---

## Phases d'exécution tactique

### Phase 4.1 : Ajout de la dépendance et installation
- **Objectif** : Rendre `tenacity` disponible dans le projet.
- **Actions** :
  - Ajouter `tenacity>=8.2.0` sous `dependencies` dans `pyproject.toml`.
  - Exécuter la commande d'installation : `.venv/Scripts/pip install tenacity`.

### Phase 4.2 : Implémentation du Retry
- **Objectif** : Implémenter la logique de retry asynchrone et de détection des erreurs transitoires dans `src/lms/router.py`.
- **Actions** :
  - Définir `is_transient_error(exception)` pour classifier les erreurs httpx, openai, google-genai et python.
  - Intégrer `AsyncRetrying` dans la méthode `LLMRouter.generate` lors de l'appel à `primary_client.generate`.

### Phase 4.3 : Tests et Validation
- **Objectif** : Vérifier que les tests existants passent et écrire des tests spécifiques pour valider la résilience et le fallback.
- **Actions** :
  - Lancer `pytest` sur la suite de tests existante.
  - Créer `tests/unit/test_router.py` pour tester le retry et le fallback.
  - Exécuter les nouveaux tests pour valider le comportement.
