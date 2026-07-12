# ADR 0004 — Services métier (Sprint 4)

Statut : validé (Sprint 4)

## Contexte

Sprint 4 ajoute la couche Services au-dessus des repositories (Sprint 3.2) : dix services (`UserService`, `ProfileService`, `SkillService`, `CompanyService`, `MissionService`, `ApplicationService`, `ContactService`, `DocumentService`, `LinkedInService`, `AuditService`) qui portent enfin les règles métier volontairement absentes des repositories (machine à états `StatutCandidature`, déduplication à l'écriture, invariants). Plusieurs choix structurants se posaient : forme des exceptions, stratégie de test, et comment honorer l'engagement pris en ADR 0003 ("chaque événement métier est persisté en un `AuditEvent`") maintenant qu'une couche capable de le faire existe.

## Décisions

### 1. Hiérarchie d'exceptions : peu de classes, génériques et paramétrées

`memory_agent/exceptions.py` définit une racine `MemoryAgentError`, trois exceptions génériques couvrant la majorité des cas (`EntityNotFoundError(entity_name, entity_id)`, `DuplicateEntityError(entity_name, field, value)`, `InvalidStatusTransitionError(entity_name, statut_actuel, statut_cible)`), et une poignée d'exceptions de validation ciblées (`InvalidTjmRangeError`, `InvalidPeriodError`, `InvalidQualificationError`, `InvalidMetricsStateError`).

**Pourquoi pas une sous-classe par agrégat** (`UserNotFoundError`, `SkillNotFoundError`, …) : redondant — les trois exceptions génériques portent déjà un contexte structuré (`entity_name`, pas seulement un message), donc `except EntityNotFoundError as e: ... e.entity_name` reste exploitable sans multiplier les classes. Rejoint CLAUDE.md (pas d'abstraction prématurée).

### 2. Tests de services : repositories SQLAlchemy réels sur SQLite en mémoire, pas de faux repositories

`tests/services/` réutilise les implémentations `SqlAlchemy*Repository` (déjà testées indépendamment, Sprint 3.2/3.3) via la fixture `session` (SQLite en mémoire, `TEST_DATABASE_URL`), plutôt que d'écrire dix implémentations `Protocol` factices en mémoire.

**Pourquoi** : les Protocols de `repositories/interfaces.py` garantissent déjà le découplage (les services ne référencent aucune classe SQLAlchemy) ; dupliquer chaque repository en une version "fake" pour les tests serait un investissement important sans bénéfice réel à l'échelle actuelle du projet (pas de besoin de swapper de backend en test). Le compromis assumé : ce sont des tests unitaires de la *logique métier*, mais ils passent par une vraie base (rapide, hermétique, sans I/O disque) plutôt que par des doublures — à revisiter si la suite devient lente ou si un besoin réel de fake repositories apparaît (ex. tests de couche API futurs).

### 3. Traçabilité : `Acteur` obligatoire sur toute méthode de service qui écrit

Chaque méthode mutante des dix services prend un paramètre `acteur: Acteur` obligatoire (mot-clé) et émet un `AuditEvent` via le helper partagé `services/_audit.py::enregistrer_evenement`, après l'écriture sur l'agrégat. Ça opérationnalise l'engagement pris en ADR 0003 §"Traçabilité" : chaque événement métier de `docs/domain-model.md` §10 correspond maintenant à un appel réel, pas seulement à une entrée de catalogue.

**Conséquence** : aucune écriture silencieuse. Un futur appelant (endpoint FastAPI, script, agent autonome) doit toujours fournir explicitement qui/quoi déclenche l'action — pas de valeur par défaut du type "acteur système" qui masquerait l'origine réelle d'un changement.

**Écart au domain model comblé** : `DéfinirPréférencesDeMission` (§12) n'avait pas d'événement correspondant en §10 — `PréférencesDeMissionModifiées` a été ajouté à `docs/domain-model.md` pour combler ce trou, découvert en implémentant `ProfileService`.

### 4. Machines à états : constantes de module dans le service concerné, pas dans les repositories ni un module partagé

`StatutCandidature` (`ApplicationService`, `_TRANSITIONS`) et `StatutPost` (`LinkedInService`, `_POST_TRANSITIONS`) sont validées par des `dict[Statut, frozenset[Statut]]` définis localement dans le fichier du service qui les utilise.

**Pourquoi pas dans les repositories** : décision déjà actée en Sprint 3.2 — les repositories restent une couche de persistance pure, sans règle métier (`docs/domain-model.md` §11, confirmé par les tests de non-régression existants). **Pourquoi pas un module `rules.py` partagé** : chaque machine à états n'est utilisée que par un seul service ; les y garder colocalisées évite un module supplémentaire pour deux constantes.

### 5. `SkillService.fusionner` : absorption des alias uniquement, pas de suppression ni de repointage

`fusionner(source_id, cible_id)` ajoute le nom et les alias de `source` comme alias de `cible`, mais **ne supprime pas** `source` et **ne repointe pas** les références existantes (`Profil.competences`, `Mission.competences_requises`) qui pointent encore vers `source_id`.

**Pourquoi** : les repositories n'exposent aucune opération de suppression (`docs/domain-model.md` §11 ne documente que `sauvegarder`/lecture), et repointer toutes les références d'un `SkillId` à travers tous les `Profil`/`Mission` d'un utilisateur nécessiterait une opération de migration en masse hors du périmètre "cas d'usage unitaire" de ce sprint. Limite assumée et documentée dans le docstring de la méthode plutôt que silencieuse.

### 6. Injection de dépendances : constructeurs simples, aucun framework

Chaque service reçoit ses dépendances (repositories typés via les `Protocol` de `repositories/interfaces.py`, jamais une classe `SqlAlchemy*Repository` concrète) par `__init__`. Aucun framework de DI, aucune dépendance à FastAPI — conforme à la contrainte du sprint. Le câblage réel (créer une `Session`, instancier les repositories concrets, les injecter dans les services) reviendra à la future couche API (FastAPI, Sprint 5), hors périmètre ici.

## Conséquences

- `agents/memory-agent/src/memory_agent/services/` : 10 services + `exceptions.py` + deux helpers internes (`_audit.py`, `_util.py`).
- `agents/memory-agent/tests/services/` : 57 tests unitaires supplémentaires (89 au total avec les 32 existants), un fichier par service, fixtures de repositories dans `tests/services/conftest.py`.
- `docs/domain-model.md` §10 légèrement enrichi (`PréférencesDeMissionModifiées`) — pas de changement de structure, juste un événement manquant ajouté.
- Ruff (y compris `T20` anti-`print()`), MyPy strict et pytest restent verts sur l'ensemble `src/` + `tests/`.
- Toujours aucun endpoint FastAPI, aucune logique IA, aucune interface utilisateur — périmètre du sprint respecté.

## Alternatives envisagées

- **Une exception par agrégat** (20+ classes) : écartée — voir décision 1.
- **Repositories factices en mémoire pour les tests de service** : écartée pour l'instant — voir décision 2.
- **Émission d'audit implicite via un décorateur/middleware** : écartée — plus "magique", moins explicite qu'un paramètre `acteur` obligatoire visible dans chaque signature ; réévaluable si le nombre de call sites devient un fardeau.
- **Suppression + repointage complet dans `SkillService.fusionner`** : écartée pour ce sprint — voir décision 5 ; à reprendre si un besoin réel de nettoyage de référentiel apparaît.
