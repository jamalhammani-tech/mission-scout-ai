# memory-agent

## Rôle

Source de vérité unique sur le profil professionnel de Jamal, ses objectifs de mission, ses préférences, et l'historique de ses candidatures. Les autres agents la consultent ; aucun ne duplique cet état.

Modèle de domaine de référence : [`docs/domain-model.md`](../../docs/domain-model.md). Choix techniques : [`docs/adr/0001-stack-persistence-memory-agent.md`](../../docs/adr/0001-stack-persistence-memory-agent.md), [`docs/adr/0002-postgresql-docker-compose.md`](../../docs/adr/0002-postgresql-docker-compose.md).

## Contenu géré

- Comptes utilisateurs (`User`) et rattachement de toute donnée personnelle à leur propriétaire.
- Profil professionnel (compétences, expériences, TJM cible, contraintes géographiques/remote).
- Référentiels partagés : compétences (`Skill`), entreprises (`Company`).
- Missions, candidatures, entretiens, contacts, documents de candidature.
- Présence LinkedIn (profil, posts, conversations).
- Tags transverses et traçabilité (`AuditEvent`).

## Statut — Sprint 3, étape 1

Couche Domain + Persistence en place (aucun endpoint, aucun service métier, aucune logique IA à ce stade) :

- Modèles SQLAlchemy 2.0 : `src/memory_agent/models/`
- Schémas Pydantic v2 : `src/memory_agent/schemas/`
- Repositories (interfaces `Protocol` + implémentation SQLAlchemy) : `src/memory_agent/repositories/`
- Migration Alembic initiale : `migrations/versions/`

## Développement

```bash
docker compose up -d           # démarre PostgreSQL (docker-compose.yml à la racine du repo)
cd agents/memory-agent
uv sync                        # installe les dépendances
uv run alembic upgrade head    # applique les migrations
```

`DATABASE_URL` (dans `config/.env`, voir `config/.env.example`) pointe par défaut vers le PostgreSQL du docker-compose local. SQLite (`sqlite:///:memory:`, constante `TEST_DATABASE_URL`) est réservé aux tests unitaires — voir [ADR 0002](../../docs/adr/0002-postgresql-docker-compose.md).

## Prochaine étape

Cas d'usage (couche service) au-dessus des repositories : validation des transitions de statut, déduplication `Skill`/`Company` à l'écriture, émission des événements métier / `AuditEvent`. Endpoints FastAPI et logique IA hors périmètre pour l'instant.
