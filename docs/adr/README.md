# Architecture Decision Records (ADR)

Depuis la validation du domain model (`docs/domain-model.md`, Sprint 2), **toute évolution structurante du projet passe par un ADR** : changement de stack, de format de persistance, ajout de dépendance lourde, écart au domain model, etc.

## Convention

- Un fichier par décision : `NNNN-titre-court.md`, numérotation séquentielle continue.
- Statut : `proposé`, `validé`, `remplacé par ADR-XXXX`.
- Sections attendues : Contexte, Décision, Conséquences, Alternatives envisagées.
- Un ADR ne se réécrit pas : s'il devient obsolète, il est marqué "remplacé" et un nouvel ADR le référence.

## Index

- [0001 — Stack et persistance du Memory Agent](0001-stack-persistence-memory-agent.md)
