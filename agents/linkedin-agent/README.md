# linkedin-agent

## Rôle

Optimiser le profil LinkedIn (titre, résumé, expériences, compétences) et proposer du contenu (posts, commentaires) aligné avec le positionnement recherché.

## Entrée

- Profil LinkedIn actuel (export ou saisie manuelle dans `data/`).
- Positionnement cible et mots-clés (via `memory-agent`).

## Sortie

- Suggestions de réécriture de sections de profil.
- Propositions de contenu à publier, stockées dans `data/`.

## Statut

Non implémenté. Décision à prendre : import du profil (manuel vs API LinkedIn, souvent restreinte).
