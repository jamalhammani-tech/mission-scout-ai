# recruiter-agent

## Rôle

Suivre le cycle de vie des candidatures : contacts recruteurs, statut par mission, relances au bon moment.

## Entrée

- Missions qualifiées (via `mission-agent`).
- Historique des échanges/candidatures (via `memory-agent`).

## Sortie

- Pipeline de candidatures à jour (statut, prochaine action, date de relance).
- Alimente `dashboard-agent`.

## Statut

Non implémenté. Décision à prendre : modèle de statuts du pipeline (ex. repéré → postulé → entretien → offre → clos).
