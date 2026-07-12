# Jamal AI Agent

Plateforme IA personnelle pour piloter ma recherche de missions IT : détection d'opportunités, optimisation du profil LinkedIn, adaptation de CV, gestion des candidatures, préparation aux entretiens.

## Vision

Un ensemble d'agents spécialisés, coordonnés, qui partagent une mémoire commune sur mon profil, mes objectifs et l'historique de mes candidatures — plutôt qu'un seul gros script monolithique.

## Architecture

```
JamalAI/
├── agents/             # Un agent = une responsabilité métier
│   ├── mission-agent/      # Recherche et qualification de missions/offres
│   ├── linkedin-agent/     # Optimisation profil + contenu LinkedIn
│   ├── cv-agent/           # Génération/adaptation de CV par mission
│   ├── recruiter-agent/    # Suivi et relance des recruteurs/candidatures
│   ├── interview-agent/    # Préparation d'entretiens (Q&A, simulation)
│   ├── dashboard-agent/    # Vue d'ensemble : pipeline, métriques, statut
│   └── memory-agent/       # Mémoire partagée (profil, préférences, historique)
├── prompts/            # Prompts versionnés, réutilisés par les agents
├── knowledge/          # Base de connaissance : profil pro, offres de référence, marché
├── data/               # Données runtime (candidatures, missions, exports)
├── docs/               # Documentation d'architecture et de décisions
├── scripts/            # Scripts d'automatisation, outillage CLI
├── tests/              # Tests unitaires et d'intégration
├── config/             # Configuration (env, paramètres agents)
├── logs/               # Logs d'exécution
├── frontend/           # Interface utilisateur (dashboard, à venir)
├── backend/            # API / orchestration des agents (à venir)
└── CLAUDE.md           # Instructions pour Claude Code sur ce projet
```

## Principes directeurs

1. **Un agent = une responsabilité.** Pas d'agent fourre-tout ; chaque agent a une entrée/sortie claire.
2. **Mémoire centralisée.** `memory-agent` est la seule source de vérité sur mon profil et l'historique — les autres agents la consultent, ne la dupliquent pas.
3. **Prompts versionnés et testables.** Les prompts vivent dans `prompts/`, hors du code, pour pouvoir être itérés et comparés.
4. **Construction incrémentale.** On avance agent par agent, avec une base testée, plutôt que de générer toute l'application d'un coup.
5. **Séparation données / code.** Rien de personnel (CV, offres, historique) ne doit être codé en dur ; tout passe par `data/` et `knowledge/`.

## État actuel

`memory-agent` (Sprint 3, étape 1) : couche Domain + Persistence en place (modèles SQLAlchemy 2, schémas Pydantic v2, migrations Alembic, repositories) — voir `agents/memory-agent/README.md`, `docs/domain-model.md` et `docs/adr/`. Pas encore d'endpoint, de service métier ni de logique IA. Les autres agents restent non implémentés.

## Prochaines étapes proposées

1. Définir le contenu de `knowledge/` (profil pro, objectifs de mission, critères de qualification).
2. Spécifier le contrat d'interface commun aux agents (entrée/sortie, format d'échange).
3. Implémenter `memory-agent` en premier (fondation dont dépendent les autres).
4. Implémenter `mission-agent` (valeur immédiate : trouver des missions).
5. Étendre ensuite vers `cv-agent`, `linkedin-agent`, `recruiter-agent`, `interview-agent`, `dashboard-agent`.

À discuter avant d'implémenter : stack technique (langage, framework d'orchestration d'agents, stockage), et sources de données pour `mission-agent` (APIs, scraping, plateformes ciblées).
