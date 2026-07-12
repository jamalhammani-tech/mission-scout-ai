# cv-agent

## Rôle

Adapter le CV de référence à une mission spécifique : mise en avant des compétences et expériences pertinentes, reformulation ciblée.

## Entrée

- CV de référence (stocké dans `knowledge/`).
- Description de la mission ciblée (issue de `mission-agent`).

## Sortie

- CV adapté (format à définir : Markdown source + export PDF/DOCX), stocké dans `data/`.

## Statut

Non implémenté. Décision à prendre : format source du CV (Markdown/YAML structuré) et moteur de rendu PDF.
