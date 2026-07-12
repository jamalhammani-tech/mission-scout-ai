# ADR 0002 — PostgreSQL via docker-compose, SQLite réservé aux tests unitaires

Statut : validé (Sprint 3)

Remplace le point "Base de données" de [ADR 0001](0001-stack-persistence-memory-agent.md).

## Contexte

ADR 0001 retenait SQLite par défaut pour démarrer sans dépendance d'infrastructure, avec `DATABASE_URL` déjà pensé pour permettre une bascule vers PostgreSQL sans changer le code applicatif (types portables : `Uuid`, `Enum(native_enum=False)`, `JSON`, index partiels dupliqués `sqlite_where`/`postgresql_where`). Cette bascule est demandée maintenant, avant même d'attaquer la couche cas d'usage/API, plutôt qu'en fin de projet.

## Décision

- **PostgreSQL** devient le moteur de développement et de production, fourni par un service `postgres` dans `docker-compose.yml` (racine du repo) : image `postgres:16-alpine`, volume nommé pour la persistance, healthcheck `pg_isready`.
- **Driver** : `psycopg` v3 (`psycopg[binary]`), dialecte SQLAlchemy `postgresql+psycopg://`.
- **SQLite est réservé aux tests unitaires** — plus de fallback silencieux vers un fichier `data/memory-agent.db` : `get_database_url()` (`memory_agent/config.py`) retourne désormais par défaut l'URL PostgreSQL du docker-compose local ; une constante `TEST_DATABASE_URL = "sqlite:///:memory:"` est exposée séparément pour que les futurs tests construisent explicitement un engine SQLite en mémoire, sans passer par `get_database_url()`.
- Identifiants de dev par défaut (`memory_agent`/`memory_agent`, base `memory_agent`, port `5432`) : définis dans `docker-compose.yml` avec substitution `${VAR:-défaut}`, surchageables via `config/.env` (voir `config/.env.example`).
- Aucun changement aux modèles/migrations : ils étaient déjà écrits de façon portable (ADR 0001) et n'ont pas eu besoin d'être modifiés pour ce changement de moteur.

## Conséquences

- Le développement local nécessite désormais Docker (`docker compose up -d` avant `alembic upgrade head`). Documenté dans `agents/memory-agent/README.md`.
- Les tests unitaires (à écrire dans une étape ultérieure) doivent créer leur propre engine SQLite en mémoire (`create_engine(TEST_DATABASE_URL)` + `Base.metadata.create_all`) plutôt que de dépendre d'une base PostgreSQL démarrée — ils restent rapides et sans dépendance d'infrastructure. Ils ne doivent en revanche pas être utilisés comme garantie de compatibilité PostgreSQL (types, contraintes, comportement des index partiels) : un test d'intégration contre le PostgreSQL réel de `docker-compose.yml` reste nécessaire pour ça.
- Non vérifié en conditions réelles dans cette session : le fichier `docker-compose.yml` a été validé syntaxiquement (`docker compose config`) et le démon Docker a pu être démarré, mais `docker compose up` échoue dans ce sandbox car la politique réseau de l'environnement bloque le pull de l'image (`production.cloudfront.docker.com` hors liste d'autorisation). Les migrations réutilisent des types déjà pensés pour être portables (ADR 0001) ; **à confirmer par un `docker compose up -d && uv run alembic upgrade head` en local**, où l'accès à Docker Hub n'est pas restreint.
- `data/memory-agent.db` (fichier SQLite généré par ADR 0001) devient obsolète pour le flux normal ; il n'était de toute façon jamais commité (`data/**` dans `.gitignore`).

## Alternatives envisagées

- **Garder SQLite en dev et PostgreSQL seulement en prod** : écarté — fait diverger le comportement testé en local de celui de prod (types, contraintes d'unicité partielles, sensibilité à la casse) ; demandé explicitement par l'utilisateur d'unifier sur PostgreSQL dès le dev.
- **Postgres géré hors Docker (service système)** : écarté — moins reproductible d'une machine à l'autre, docker-compose donne une commande unique et un état jetable/réinitialisable.
