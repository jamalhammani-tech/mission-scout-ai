# ADR 0003 — Developer Experience & Quality (Sprint 3.3)

Statut : validé (Sprint 3.3)

## Contexte

Avant d'attaquer les Services métier (Sprint 4), le projet a besoin de garde-fous techniques : qualité de code automatisée, CI, logging exploitable, configuration par environnement. Plusieurs choix structurants se posaient : où faire vivre l'outillage (racine du repo vs par agent), quelle bibliothèque de logging, comment intégrer `pydantic-settings`. Cet ADR les documente, conformément à la règle établie en Sprint 3.2 ("toute évolution passe par un ADR").

## Décisions

### 1. Outillage scopé par agent, pas de workspace Python à la racine

`ruff`, `mypy`, `pytest` sont configurés dans `agents/memory-agent/pyproject.toml` (pas de config Python à la racine du repo). Pre-commit et la CI GitHub Actions vivent à la racine (`.pre-commit-config.yaml`, `.github/workflows/ci.yml`) mais exécutent tout depuis `agents/memory-agent/` (`working-directory` / hooks locaux avec `cd`).

**Pourquoi** : un seul agent a du code Python aujourd'hui. Introduire un `uv workspace` racine (`[tool.uv.workspace]`) pour un seul membre serait de la sur-ingénierie prématurée (cf. CLAUDE.md — construire de façon incrémentale). Le pattern "un agent = un projet Python autonome" reste cohérent avec la convention `agents/<nom> = une responsabilité unique`.

**Conséquence assumée** : quand un deuxième agent Python apparaîtra, ce choix devra être revisité — soit dupliquer le pattern (pyproject.toml + config qualité par agent), soit basculer vers un workspace uv partagé. Non tranché ici, à réévaluer à ce moment-là.

### 2. Pre-commit : hooks locaux (`uv run ...`), pas les mirrors GitHub officiels

`.pre-commit-config.yaml` utilise exclusivement des hooks `repo: local` qui invoquent `uv run ruff`/`mypy`/`pytest` depuis `agents/memory-agent`, plutôt que `ruff-pre-commit`/`mirrors-mypy`.

**Pourquoi** : évite un écart de version entre l'outil exécuté par pre-commit et celui pinné dans `uv.lock` (source de vérité unique) ; évite aussi une dépendance réseau supplémentaire au moment du hook (ce sandbox de développement a déjà montré des restrictions d'accès à certains registries — cf. ADR 0002). `ruff`/`mypy`/`pytest` s'exécutent au commit ; `pytest` est réservé au stage `pre-push` (suite plus lente, on ne veut pas ralentir chaque commit local).

**Installation** (une fois) : `cd agents/memory-agent && uv run pre-commit install --hook-type pre-commit --hook-type pre-push`.

### 3. CI : installation de uv par script officiel, pas l'action marketplace

`.github/workflows/ci.yml` installe `uv` via `curl -LsSf https://astral.sh/uv/install.sh | sh` plutôt que via l'action `astral-sh/setup-uv`.

**Pourquoi** : le script d'installation est stable dans le temps ; épingler une version d'action marketplace sans pouvoir la vérifier en environnement sandboxé est un risque évitable. Migration vers l'action possible plus tard pour bénéficier du cache de dépendances — non bloquant.

Déclenchement : `push` et `pull_request` sans restriction de branche (demande explicite "à chaque Push et Pull Request"), au prix de doubles exécutions sur les PR internes au repo — acceptable à l'échelle du projet actuel.

### 4. Logging structuré : stdlib `logging` + formatter JSON maison, pas de nouvelle dépendance

`memory_agent/logging_config.py` fournit un `JsonFormatter` (une ligne JSON par entrée : timestamp, level, logger, message, `exc_info` si présent, tout champ `extra` passé à l'appel) et `configure_logging()`, piloté par `Settings` (niveau et format résolus selon l'environnement).

**Pourquoi pas `structlog`** : le besoin ("logging structuré", pas de `print()`, configuration centralisée) est couvert par la stdlib pour un projet mono-utilisateur à ce stade. Ajouter une dépendance pour ça serait prématuré (CLAUDE.md — pas de dépendance lourde sans validation). Réévaluable si le besoin de contexte propagé (contextvars, bind de logger) devient réel avec les futurs Services métier.

`print()` est interdit par construction : la règle ruff `T20` (flake8-print) est activée dans `[tool.ruff.lint].select`, donc tout `print()`/`pprint()` fait échouer `ruff check` (et donc le hook pre-commit et la CI).

### 5. Configuration centralisée avec `pydantic-settings`

`memory_agent/settings.py` remplace l'ancien `config.py` (Sprint 3.2, lecture `os.getenv` ad hoc) par une classe `Settings(BaseSettings)` unique, avec :

- `environment: Environment` (`development` / `test` / `production`), lu depuis `ENVIRONMENT`.
- Résolution différenciée par environnement plutôt que valeurs statiques : `resolved_database_url` (Postgres par défaut, SQLite forcé si `environment=test` et qu'aucun `DATABASE_URL` explicite n'est fourni — cohérent avec ADR 0002), `resolved_log_level` (`DEBUG` en dev, `INFO` ailleurs sauf override), `resolved_log_format` (`console` en dev, `json` ailleurs sauf override).
- Garde-fou : `environment=production` sans `DATABASE_URL` explicite lève une erreur de validation au démarrage plutôt que de retomber silencieusement sur les identifiants de dev du docker-compose local.

`db.py` et `migrations/env.py` ont été mis à jour pour consommer `get_settings().resolved_database_url` au lieu de l'ancien `get_database_url()`.

## Conséquences

- `config.py` (Sprint 3.2) est supprimé, remplacé par `settings.py` — pas de couche de compatibilité conservée (CLAUDE.md — pas de shim de rétrocompatibilité pour du code interne non publié).
- `agents/memory-agent/pyproject.toml` gagne `pydantic-settings`, `ruff`, `mypy`, `pre-commit` (dev), et les sections `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`.
- Une suite de tests unitaires apparaît (`agents/memory-agent/tests/`, 32 tests) : elle porte sur la couche Domain + Persistence existante (repositories, settings, logging), toujours sans aucune règle métier ni service — conformément au périmètre de ce sprint.
- Le smoke test manuel ad hoc du Sprint 3.2 (non commité) est désormais remplacé par cette suite pytest committée.
- `mypy --strict` est activé sur `src/` et `tests/` ; un marqueur `py.typed` a été ajouté à `memory_agent` pour que mypy analyse correctement le package quand il est importé "comme une dépendance installée" (cas des tests).
- Non vérifié en conditions réelles : le workflow GitHub Actions n'a pas pu être déclenché depuis ce sandbox (pas d'accès à l'API GitHub Actions) ; sa syntaxe YAML a été validée localement et sa logique reproduit exactement les commandes exécutées avec succès en local (`uv sync`, `ruff check`, `ruff format --check`, `mypy`, `pytest`).

## Alternatives envisagées

- **uv workspace racine dès maintenant** : écarté — un seul membre existant, complexité non justifiée (cf. décision 1).
- **`ruff-pre-commit`/`mirrors-mypy`** : écarté au profit de hooks locaux — voir décision 2.
- **`structlog`** : écarté pour l'instant — voir décision 4. À reconsidérer si les Services métier (Sprint 4) ont besoin de contexte de log propagé entre appels.
- **Root `pyproject.toml` partagé pour la config ruff/mypy** : écarté, cohérent avec la décision 1 (pas de projet Python racine).
