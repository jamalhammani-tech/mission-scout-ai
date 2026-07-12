# memory-agent

## Rôle

Source de vérité unique sur le profil professionnel de Jamal, ses objectifs de mission, ses préférences, et l'historique de ses candidatures. Les autres agents la consultent ; aucun ne duplique cet état.

Modèle de domaine de référence : [`docs/domain-model.md`](../../docs/domain-model.md). Choix techniques : [`docs/adr/`](../../docs/adr/) (0001 stack/persistence, 0002 PostgreSQL/docker-compose, 0003 Developer Experience & Quality).

## Contenu géré

- Comptes utilisateurs (`User`) et rattachement de toute donnée personnelle à leur propriétaire.
- Profil professionnel (compétences, expériences, TJM cible, contraintes géographiques/remote).
- Référentiels partagés : compétences (`Skill`), entreprises (`Company`).
- Missions, candidatures, entretiens, contacts, documents de candidature.
- Présence LinkedIn (profil, posts, conversations).
- Tags transverses et traçabilité (`AuditEvent`).

## Statut — Sprint 3.3 (Developer Experience & Quality)

Couche Domain + Persistence (Sprint 3.2) inchangée, complétée par l'outillage qualité (aucun endpoint, aucun service métier, aucune logique IA à ce stade) :

- Modèles SQLAlchemy 2.0 : `src/memory_agent/models/`
- Schémas Pydantic v2 : `src/memory_agent/schemas/`
- Repositories (interfaces `Protocol` + implémentation SQLAlchemy) : `src/memory_agent/repositories/`
- Migration Alembic initiale : `migrations/versions/`
- Configuration centralisée par environnement (`development`/`test`/`production`) : `src/memory_agent/settings.py`
- Logging structuré JSON, configuration centralisée : `src/memory_agent/logging_config.py`
- Suite de tests unitaires : `tests/` (SQLite en mémoire, voir ADR 0002/0003)
- Qualité : Ruff (lint + format), MyPy (strict), pre-commit, CI GitHub Actions

## Développement

```bash
docker compose up -d           # démarre PostgreSQL (docker-compose.yml à la racine du repo)
cd agents/memory-agent
uv sync                        # installe les dépendances (dont les outils dev)
uv run alembic upgrade head    # applique les migrations
```

`DATABASE_URL` (dans `config/.env`, voir `config/.env.example`) pointe par défaut vers le PostgreSQL du docker-compose local. SQLite (`sqlite:///:memory:`) est réservé aux tests unitaires — voir [ADR 0002](../../docs/adr/0002-postgresql-docker-compose.md). `ENVIRONMENT` (`development`/`test`/`production`) pilote les valeurs par défaut de connexion et de logging — voir [ADR 0003](../../docs/adr/0003-developer-experience-quality.md).

### Qualité de code

```bash
uv run ruff check .            # lint
uv run ruff format .           # format
uv run mypy src tests          # typage statique (strict)
uv run pytest                  # tests unitaires
```

### Pre-commit (une fois par poste de dev)

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Ruff et MyPy tournent à chaque commit ; Pytest tourne avant chaque push (suite plus lente). La CI GitHub Actions (`.github/workflows/ci.yml`, racine du repo) exécute les trois à chaque push et pull request.

## Prochaine étape

Cas d'usage (couche service) au-dessus des repositories : validation des transitions de statut, déduplication `Skill`/`Company` à l'écriture, émission des événements métier / `AuditEvent`. Endpoints FastAPI et logique IA hors périmètre pour l'instant.
