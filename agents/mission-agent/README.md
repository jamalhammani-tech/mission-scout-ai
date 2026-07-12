# mission-agent

## Rôle

Rechercher, collecter et qualifier des missions/offres IT pertinentes par rapport au profil et aux critères définis dans `memory-agent`.

## Entrée

- Profil et critères de recherche (via `memory-agent` : compétences, TJM cible, localisation/remote, secteurs).
- Sources de missions (à définir : APIs job boards, plateformes freelance, scraping ciblé).

## Sortie

- Liste de missions qualifiées (score de pertinence, lien, critères correspondants/manquants).
- Écrit dans `data/` pour consommation par `dashboard-agent` et `recruiter-agent`.

## Statut

Non implémenté. Décisions à prendre : sources de données, fréquence de collecte, critère de scoring.
