# cv-agent

## Rôle

Premier cas d'usage complet du produit : importer un CV (PDF/DOCX), l'analyser via l'API Anthropic, et alimenter le profil professionnel via les Services du Memory Agent (`memory-agent`, dépendance locale).

## Commande

```bash
cd agents/cv-agent
uv sync
uv run import-cv mon_cv.pdf --email jamal@example.com
```

`--email` identifie le propriétaire du profil (ou variable d'env `CV_AGENT_USER_EMAIL`) ; l'utilisateur est créé s'il n'existe pas encore (`--nom` optionnel, sinon le nom détecté dans le CV). `ANTHROPIC_API_KEY` doit être défini dans `config/.env` ou l'environnement.

## Ce que fait la commande (MVP)

1. Extrait le texte du PDF (`pdfplumber`) ou du DOCX (`python-docx`).
2. Envoie le texte à Claude (tool use, prompt dans [`prompts/cv-agent/extraction-cv.md`](../../prompts/cv-agent/extraction-cv.md)) pour en extraire nom, titre, expériences, compétences, technologies, certifications, langues, secteurs, et un résumé professionnel.
3. Crée (ou réutilise) l'utilisateur et le profil via `UserService`/`ProfileService`.
4. Crée/déduplique chaque compétence et technologie via `SkillService`, les rattache au profil.
5. Enregistre chaque expérience via `ProfileService.ajouter_experience`.
6. Enregistre le CV lui-même comme `Document` via `DocumentService`.
7. Affiche un résumé de l'import dans le terminal.

## Limites assumées (MVP)

- **Certifications, langues, secteurs ne sont pas persistés** : le domain model actuel (`docs/domain-model.md`) n'a pas de champ dédié sur `Profil`. Ils sont extraits et affichés dans le résumé terminal, pas enregistrés en base — décision explicite pour livrer vite (à ajouter au domain model si le besoin se confirme).
- **Pas de mise à jour du titre/résumé sur un profil déjà existant** : un second import pour le même utilisateur ajoute compétences/expériences mais ne réécrit pas `titre`/`resume`.
- **Pas de déduplication des expériences** : réimporter le même CV deux fois duplique les expériences (les compétences, elles, sont dédupliquées par `SkillService`/`ProfileService.ajouter_competence`).
- **Pas d'OCR** : un PDF scanné (image) échoue avec une erreur claire plutôt que d'être traité.
- **Pas de rattachement des entreprises au référentiel `Company`** : l'employeur de chaque expérience est stocké en texte libre (`entreprise_nom`), pas via `CompanyService`.

## Développement

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src tests
uv run pytest
```

Tests : `text_extraction` couvert par des fixtures PDF/DOCX générées à la volée ; `import_cv` couvert par un `FakeLlmExtractor` (aucun appel réseau réel dans les tests) contre les vrais Services memory-agent sur SQLite en mémoire — même stratégie que `memory-agent` (ADR 0004).

## Statut

MVP fonctionnel. Prochaine étape naturelle : CV generation/adaptation vers une mission (sens inverse, périmètre historique de cv-agent).
