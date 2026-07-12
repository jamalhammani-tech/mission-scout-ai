# mission-agent (Career Scout Agent)

## Rôle

Assiste la recherche de missions IT sans automatiser d'action sur les plateformes : import manuel d'une annonce, analyse IA, calcul d'un score de matching avec le profil (`memory-agent`), identification des compétences manquantes, et rapport clair dans le terminal.

Contraintes respectées (voir `CLAUDE.md`) : pas de scraping agressif, pas d'automatisation des connexions/messages LinkedIn, pas de contournement des protections des sites. Toute candidature ou prise de contact reste manuelle.

## Sprint 5.1 (implémenté)

- Import manuel d'une mission : `--url` (une requête HTTP ciblée, ponctuelle) ou `--texte` (collé directement).
- Analyse IA de l'annonce (Anthropic, tool use) → informations structurées (titre, entreprise, lieu, type de contrat, TJM, compétences requises, résumé).
- Score de matching avec le profil (80% couverture des compétences requises, comparaison par ID de `Skill` — pas de matching texte — + 20% compatibilité TJM).
- Identification des compétences manquantes et des écarts (TJM, type de contrat).
- Décision : `Postuler` (≥ 70%) / `À étudier` (≥ 40%) / `À ignorer`.
- Enregistrement de la mission dans le Memory Agent (dédupliquée par URL ou hash du texte collé), qualifiée automatiquement selon la décision.
- Rapport terminal.

**Pas encore développé** (Sprint 5.2 et suivants) : génération de CV adapté, génération de message de prise de contact, connecteurs multi-plateformes, automatisation d'actions.

## Commande

```bash
cd agents/mission-agent
uv sync
uv run scout import-mission --texte "..." --email jamal@example.com
uv run scout import-mission --url "https://..." --email jamal@example.com
```

`--email` identifie le propriétaire du profil (ou variable d'env `MISSION_AGENT_USER_EMAIL`). Le profil doit déjà exister (`uv run import-cv ...` dans `cv-agent`) : le score de matching n'a pas de sens sans profil de référence. `ANTHROPIC_API_KEY` doit être défini dans `config/.env` ou l'environnement.

## Ce que fait la commande

1. Récupère le texte de l'annonce : `--texte` directement, ou `--url` via une unique requête HTTP transparente (`httpx`, User-Agent identifiable, pas d'imitation de navigateur) suivie d'une extraction de texte HTML (`BeautifulSoup`). Si l'URL échoue (site protégé, JS requis, etc.), l'erreur est claire et invite à utiliser `--texte`.
2. Envoie le texte à Claude (tool use, prompt dans [`prompts/mission-agent/analyse-mission.md`](../../prompts/mission-agent/analyse-mission.md)) pour en extraire les informations structurées (`AnalyseMission`).
3. Résout chaque compétence requise en `Skill` via `SkillService.referencer_ou_reutiliser` (dédup par nom/alias déjà en place côté memory-agent).
4. Calcule le score de matching (`mission_agent.matching.calculer_matching`, fonction pure, sans I/O) en comparant les `skill_id` requis à ceux du profil, et le TJM proposé au `tjm_min` des critères de qualification du profil.
5. Enregistre (ou retrouve, si déjà importée) la mission via `MissionService.enregistrer_mission_decouverte`, puis la qualifie (`QUALIFIEE`/`ECARTEE`) selon la décision.
6. Affiche le rapport dans le terminal : score, décision, points forts, écarts, compétences manquantes, résumé.

## Limites assumées (MVP)

- **`--url` ne fonctionne que sur des pages simples, accessibles sans authentification et sans rendu JS** : une seule requête HTTP, pas de navigateur headless, pas de contournement de protection. En pratique beaucoup de job boards nécessitent `--texte` (copier-coller manuel de l'annonce).
- **Le profil doit déjà exister** : pas de création de profil à la volée depuis mission-agent (responsabilité de `cv-agent`).
- **Ré-analyser une annonce déjà connue refait un appel IA** avant de détecter le doublon (déduplication uniquement à l'enregistrement, pas avant l'analyse) : acceptable pour le MVP, à optimiser si le coût devient sensible.
- **Le type de contrat n'entre pas dans le score** : c'est une information ajoutée aux écarts, pas un facteur de pondération.

## Développement

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src tests
uv run pytest
```

Tests : `matching` couvert par des tests de fonctions pures (aucune I/O) ; `text_extraction` par un `httpx.get` monkeypatché ; `llm_analysis` par les cas de désimbrication de la réponse Anthropic (même stratégie que `cv-agent`) ; `import_mission` par un `FakeAnalyseurMission` contre les vrais Services memory-agent sur SQLite en mémoire — même stratégie que `memory-agent`/`cv-agent` (ADR 0004).

## Validation réelle

Testé de bout en bout avec PostgreSQL local, l'API Anthropic réelle et le profil réel (51 compétences) : `--texte` fonctionne intégralement (analyse → score → décision → persistance → déduplication au second import). `--url` échoue dans cet environnement sandboxé (accès réseau restreint à `anthropic.com` et aux registres de paquets) — comportement attendu, à revalider en usage réel.

## Statut

MVP Sprint 5.1 fonctionnel. Prochaine étape (Sprint 5.2, après validation par l'utilisateur) : génération du CV adapté et du message de prise de contact.
