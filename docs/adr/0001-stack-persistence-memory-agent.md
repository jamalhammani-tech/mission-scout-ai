# ADR 0001 — Stack et persistance du Memory Agent

Statut : validé (Sprint 3, étape 1)

## Contexte

`docs/domain-model.md` (validé) définit le domaine du Memory Agent mais ne fixe aucun choix technique. Pour construire la couche Domain + Persistence (Sprint 3, étape 1 : modèles SQLAlchemy, schémas Pydantic, migrations Alembic, repositories), plusieurs choix structurants devaient être tranchés : gestionnaire de projet Python, moteur de base de données, stratégie d'identifiants, style de mapping ORM, et organisation des tags/traçabilité en tables.

Ces choix ont été proposés via `AskUserQuestion` (gestionnaire de projet, moteur de BDD) sans réponse obtenue ; ils sont donc actés ici par défaut, documentés, et réversibles sans changement de domaine si besoin.

## Décision

- **Gestionnaire de projet** : [uv](https://docs.astral.sh/uv/). Déjà disponible dans l'environnement, rapide, un seul `pyproject.toml` + `uv.lock`.
- **Langage/runtime** : Python 3.11, package `memory_agent` en layout `src/`, build backend `hatchling`.
- **ORM** : SQLAlchemy 2.0 en style déclaratif `Mapped`/`mapped_column`, moteur **synchrone** (pas d'async pour ce sprint — pas de besoin identifié, cf. YAGNI).
- **Base de données** : SQLite par défaut, fichier unique dans `data/memory-agent.db` (cohérent avec la convention `data/` du projet, déjà exclu de git). L'URL de connexion est configurable via `DATABASE_URL` (voir `config/.env.example`) — SQLAlchemy abstrait le moteur, une migration vers PostgreSQL ne nécessiterait pas de changement de code, seulement quelques ajustements d'index (voir Conséquences).
- **Identifiants** : UUID4 pour toutes les clés primaires (type portable `sqlalchemy.Uuid`), plutôt que des entiers auto-incrémentés.
- **Enums** : enums Python (`str, Enum`) stockés en base via `sqlalchemy.Enum(..., native_enum=False)` — chaînes portables, pas de type ENUM natif Postgres (éviterait une migration de schéma spécifique au moteur).
- **Tags** (`docs/domain-model.md` §7) : une table `tags` (référentiel dédupliqué par `(libelle, catégorie)`) + une table d'association polymorphe `entity_tags` (`entity_type`, `entity_id`), plutôt que sept tables de jointure dédiées. Pas de relation ORM cascade sur cette association (elle est polymorphe, donc pas de FK réelle possible) : la synchronisation est gérée explicitement par un helper partagé (`repositories/_tags.py`), appelé par chaque repository concerné.
- **AuditEvent** (`docs/domain-model.md` §9) : table dédiée, immuable par construction — le repository n'expose volontairement aucune méthode de mise à jour/suppression (contrainte au niveau de l'interface, pas d'un trigger DB).
- **Repositories** : interfaces définies comme `typing.Protocol` (typage structurel, `repositories/interfaces.py`), implémentations SQLAlchemy dans des modules séparés — chaque `sauvegarder(...)` persiste l'agrégat complet (racine + enfants), les collections enfants étant resynchronisées par remplacement (`cascade="all, delete-orphan"` + rapprochement par identifiant).

## Conséquences

- Aucune dépendance lourde ajoutée au-delà de `sqlalchemy`, `alembic`, `pydantic`, `python-dotenv` (+ `pytest` en dev, non utilisé dans cette étape).
- SQLite convient à un usage mono-utilisateur mais limite l'écriture concurrente ; si `backend/` doit servir plusieurs requêtes simultanées à terme, une migration vers PostgreSQL sera nécessaire (ADR à part entière le moment venu).
- Deux index uniques partiels utilisent `sqlite_where`/`postgresql_where` (déduplication `Mission`/`Contact` par référence externe quand elle est non nulle) : portables entre les deux moteurs, mais à revalider si un troisième moteur est envisagé.
- Les repositories ne contiennent aucune règle métier (pas de validation de transition de statut, pas de déduplication applicative `Skill`/`Company` en écriture) : c'est un choix délibéré pour respecter le périmètre de l'étape 1 ("Domain + Persistence" uniquement) — ces règles seront portées par une future couche de cas d'usage (Sprint 3, étape suivante).
- Le point 3 des « points à valider » de `docs/domain-model.md` (Mission ↔ Company) et le point 7 (tags globaux sur `Company`, référentiel partagé) restent ouverts ; le schéma actuel ne les préjuge pas (un seul `company_id` sur `Mission`, tags `Company` non filtrés par propriétaire puisque `Company` n'a pas de colonne `user_id`).

## Alternatives envisagées

- **PostgreSQL dès le départ** : écarté pour cette étape — ajoute une dépendance d'infrastructure (serveur à faire tourner) sans bénéfice pour un usage mono-utilisateur actuel ; réversible via `DATABASE_URL` le moment venu.
- **poetry** au lieu de `uv` : équivalent fonctionnellement, `uv` retenu pour sa rapidité et sa simplicité (pas de choix bloquant, changement de tooling sans impact sur le domaine si besoin de revenir dessus).
- **Sept tables de jointure dédiées pour les tags** (une par entité taguable) : plus proche d'un mapping ORM « classique » avec relations cascade automatiques, mais duplique la même structure sept fois pour un besoin strictement transverse ; écarté au profit d'une table polymorphe unique + helper partagé.
- **Event sourcing complet** pour `AuditEvent` : écarté — le domain model (§9) précise explicitement un "journal append-only simple", pas une source de vérité reconstructible.
