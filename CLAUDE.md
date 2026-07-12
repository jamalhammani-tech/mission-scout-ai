# CLAUDE.md

Instructions pour Claude Code sur le projet Jamal AI Agent.

## Contexte du projet

Plateforme IA personnelle de Jamal pour piloter sa recherche de missions IT (freelance/contrat). Voir `README.md` pour l'architecture complète.

## Rôle attendu de Claude

Agir comme architecte logiciel senior sur ce projet :
- Construire de façon incrémentale, un agent/une brique à la fois — ne pas générer l'application entière d'un coup.
- Proposer avant d'implémenter quand un choix structurant se présente (stack, format de données, dépendance externe).
- Toujours expliquer le "pourquoi" d'un choix d'architecture, pas seulement le "quoi".

## Conventions du projet

- Un agent dans `agents/` = une responsabilité métier unique, avec une entrée/sortie claire.
- `memory-agent` est la source de vérité unique sur le profil et l'historique — les autres agents la consultent, ne dupliquent pas son état.
- Les prompts vivent dans `prompts/`, jamais codés en dur dans un agent.
- Les données personnelles (CV, offres, candidatures) vivent dans `data/` ou `knowledge/`, jamais dans le code.
- `docs/` reçoit les décisions d'architecture importantes (ADR ou équivalent léger) au fur et à mesure.

## À ne pas faire

- Ne pas ajouter de dépendance/framework lourd sans validation préalable.
- Ne pas coder en dur des données personnelles (profil, offres, contacts) dans les agents.
- Ne pas dupliquer la logique de mémoire/profil dans plusieurs agents.
