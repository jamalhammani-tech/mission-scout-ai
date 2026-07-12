# Domain Model — Memory Agent

Statut : proposition, en attente de validation. Aucune implémentation à ce stade.

## Pourquoi ce document

`memory-agent` est désigné comme la source de vérité unique de la plateforme (voir `README.md`, `CLAUDE.md`). Avant de l'implémenter, on fixe son modèle de domaine : quelles sont les notions métier qu'il porte, comment elles s'articulent, et quel contrat il expose aux autres agents (`mission-agent`, `cv-agent`, `linkedin-agent`, `recruiter-agent`, `interview-agent`, `dashboard-agent`).

Le domaine couvert ici est délimité par ce que `memory-agent` possède réellement : le **profil** de Jamal et l'**historique de sa recherche de mission** (missions vues, candidatures, entretiens, contacts). Il ne couvre pas la logique de scraping (`mission-agent`), de génération de CV (`cv-agent`) ou de rendu (`frontend`/`dashboard-agent`) — ces agents consomment le modèle ci-dessous, ils ne le dupliquent pas.

---

## 1. Entités métier

Une entité a une identité stable et un cycle de vie (elle change d'état dans le temps, mais reste "la même").

| Entité | Description |
|---|---|
| **Profil** | Identité professionnelle de Jamal : titre, résumé, compétences, expériences, préférences de mission. Racine de tout le domaine — il n'en existe qu'une seule instance (application mono-utilisateur). |
| **Expérience** | Une expérience professionnelle passée (mission ou poste) : entreprise/client, intitulé, période, technologies utilisées, réalisations. |
| **Mission** | Une opportunité détectée (par `mission-agent`) : offre de mission/poste IT, avec sa description, son client, sa source, son TJM annoncé. Existe indépendamment de toute candidature — Jamal peut voir une mission sans y postuler. |
| **Candidature** | L'acte de postuler à une `Mission` donnée. Porte le statut du pipeline et son historique. C'est l'entité pivot du suivi (repéré → postulé → entretien → offre → clos). |
| **Entretien** | Un entretien réalisé ou planifié, rattaché à une `Candidature`. Porte la préparation et le compte-rendu. |
| **Contact** | Une personne rencontrée dans le processus : recruteur, manager, cooptation. Peut être associée à plusieurs missions/candidatures dans le temps. |

## 2. Relations entre entités

```
Profil (1) ──── compétences/expériences intégrées (pas de relation externe : il consulte, on ne le référence pas)

Mission (1) ──< Candidature (0..1)         une mission donne lieu à au plus une candidature active
Candidature (1) ──< Entretien (0..n)        une candidature peut comporter plusieurs entretiens
Candidature (n) ──> Contact (0..n)          une candidature implique un ou plusieurs contacts
Mission (n) ──> Contact (0..n)              un contact peut être source/point d'entrée d'une mission
Contact (1) ──< Candidature (0..n)          un contact revient sur plusieurs candidatures dans le temps
```

Points clés :
- **Mission** et **Candidature** sont deux entités distinctes et non fusionnées : une mission peut être écartée sans jamais devenir une candidature, et l'historique de qualification (pertinente/écartée) doit survivre même sans candidature.
- **Profil** ne référence rien d'autre : c'est un point de lecture pour les autres agents, pas un nœud du pipeline de candidature.
- **Contact** est indépendant du cycle de vie d'une candidature : un recruteur peut revenir sur une mission ultérieure.

## 3. Responsabilités de chaque entité

- **Profil**
  - Garantir la cohérence des données professionnelles (pas de doublon de compétence, dates d'expérience valides).
  - Exposer les critères de qualification courants utilisés par `mission-agent`.
  - Être la seule entité modifiable pour tout ce qui touche à l'identité professionnelle (aucun autre agent ne réécrit le profil directement).
- **Expérience**
  - Décrire une période professionnelle passée de façon autonome (utilisable telle quelle par `cv-agent`).
- **Mission**
  - Conserver les données brutes/qualifiées d'une opportunité, indépendamment de la décision d'y postuler.
  - Porter le résultat de qualification (score, critères correspondants/manquants) produit par `mission-agent`.
- **Candidature**
  - Détenir le statut courant du pipeline et faire respecter les transitions valides (ex. impossible de passer de "postulé" à "entretien réalisé" sans passer par "entretien planifié").
  - Historiser chaque changement de statut (traçabilité pour `dashboard-agent`).
  - Référencer le document (CV) utilisé, sans en porter le contenu (propriété de `cv-agent`/`data/`).
- **Entretien**
  - Porter la préparation (généré par `interview-agent`, référencé ici) et le compte-rendu post-entretien.
- **Contact**
  - Centraliser les coordonnées et l'historique relationnel avec une personne, pour éviter les doublons entre agents.

## 4. Agrégats

Un agrégat définit une frontière de cohérence : on ne modifie ses entités internes qu'à travers sa racine, et les autres agrégats ne le référencent que par identifiant.

| Agrégat (racine en gras) | Entités/VO inclus | Invariants portés |
|---|---|---|
| **Profil** | Expérience(s), Compétence (VO), PréférencesDeMission (VO), CritèresDeQualification (VO) | Un seul profil actif ; compétences non dupliquées ; préférences toujours cohérentes (ex. TJM min ≤ TJM max). |
| **Mission** | StatutDeQualification (VO), Source (VO) | Une mission qualifiée porte toujours un score et une justification. |
| **Candidature** | Entretien(s), HistoriqueStatut (VO, liste d'événements horodatés) | Transitions de statut respectant la machine à états du pipeline ; toujours rattachée à exactement une `MissionId`. |
| **Contact** | ContactInfo (VO) | Email ou identifiant LinkedIn unique par contact. |

`Candidature` référence `MissionId`, `ProfilId` (implicite, un seul profil) et `ContactId[]` — jamais les objets complets, pour préserver l'indépendance des agrégats.

## 5. Value Objects

Sans identité propre ; deux VO avec les mêmes attributs sont interchangeables ; immuables.

- **Competence** — nom, catégorie (langage, framework, cloud, méthode…), niveau (junior/confirmé/expert), années d'expérience associées.
- **TJM** — montant, devise, unité (jour/heure), et éventuellement `TJM { min, max }` pour une fourchette cible.
- **PériodeDisponibilité** — date de début, date de fin optionnelle (mission en cours vs. disponible immédiatement).
- **LocalisationPréférence** — remote (total/partiel/non), ville de base, périmètre de déplacement accepté.
- **CritèresDeQualification** — agrégat de règles utilisées par `mission-agent` : TJM minimum, remote requis, technologies recherchées/exclues, types de contrat acceptés (freelance/portage/CDI), secteurs exclus.
- **PériodeExpérience** — date de début, date de fin (ou "en cours").
- **StatutCandidature** — valeur énumérée avec transitions autorisées : `Repérée → Postulée → EntretienPlanifié → EntretienRéalisé → OffreReçue → Acceptée` ou `… → Refusée / SansRéponse / Abandonnée` à toute étape.
- **StatutDeQualification** — `NonQualifiée / Qualifiée / Écartée`, avec score et motif.
- **Source** — origine d'une mission ou d'un contact (LinkedIn, plateforme freelance, réseau personnel, cooptation, candidature spontanée).
- **ContactInfo** — email, téléphone, URL LinkedIn.
- **RéférenceDocument** — pointeur logique vers un fichier de `data/` (chemin ou identifiant), jamais le contenu.

## 6. Événements métier

Émis par les agrégats à chaque changement d'état significatif ; consommés par les autres agents (notification, mise à jour de `dashboard-agent`, déclenchement de `cv-agent`/`interview-agent`, etc.).

- `ProfilCréé`
- `CompétenceAjoutée` / `CompétenceRetirée`
- `ExpérienceAjoutée`
- `CritèresDeQualificationModifiés`
- `MissionDécouverte` (nouvelle mission enregistrée par `mission-agent`)
- `MissionQualifiée` / `MissionÉcartée`
- `CandidatureCréée`
- `StatutCandidatureChangé` (ancien statut, nouveau statut, horodatage)
- `EntretienPlanifié`
- `EntretienRéalisé` (avec compte-rendu associé)
- `CandidatureClôturée` (refus, acceptation ou abandon — motif inclus)
- `ContactAjouté` / `ContactMisÀJour`

Ces événements sont la matière première d'un futur historique/journal consultable par `dashboard-agent`, sans que celui-ci ait à interroger chaque agrégat séparément.

## 7. Interfaces de repository

Définies au niveau conceptuel (contrat, pas de code) — un repository par agrégat, aucune fuite de logique métier vers l'infrastructure.

**ProfilRepository**
- `getProfil() -> Profil` (instance unique)
- `sauvegarder(profil: Profil) -> void`

**MissionRepository**
- `parId(id: MissionId) -> Mission | absent`
- `parSource(source: Source) -> Mission[]`
- `parStatutDeQualification(statut) -> Mission[]`
- `sauvegarder(mission: Mission) -> void`

**CandidatureRepository**
- `parId(id: CandidatureId) -> Candidature | absent`
- `parMission(id: MissionId) -> Candidature | absent`
- `parStatut(statut: StatutCandidature) -> Candidature[]`
- `listerActives() -> Candidature[]` (tout ce qui n'est pas `Clôturée`)
- `sauvegarder(candidature: Candidature) -> void`

**ContactRepository**
- `parId(id: ContactId) -> Contact | absent`
- `parEmail(email: string) -> Contact | absent`
- `sauvegarder(contact: Contact) -> void`

Chaque repository ne manipule que la racine de son agrégat (ex. on ne "sauvegarde" pas un `Entretien` seul, on sauvegarde la `Candidature` qui le contient).

## 8. Cas d'utilisation

Ce que `memory-agent` expose réellement aux autres agents — chaque cas d'usage correspond à une intention métier, pas à un CRUD brut.

**Gestion du profil**
- `ConsulterProfil` — lecture par tous les agents (compétences, préférences, critères).
- `MettreÀJourCompétences` — ajouter/retirer une compétence.
- `AjouterExpérience`
- `DéfinirCritèresDeQualification` — utilisé pour piloter `mission-agent`.
- `DéfinirPréférencesDeMission` (TJM cible, remote, disponibilité).

**Missions**
- `EnregistrerMissionDécouverte` — appelé par `mission-agent` après collecte.
- `QualifierMission` — enregistrer le résultat de scoring (qualifiée/écartée + motif).
- `ConsulterMissionsQualifiées` — pour `dashboard-agent`, `recruiter-agent`.

**Candidatures**
- `CréerCandidature` — à partir d'une `Mission` qualifiée, quand Jamal décide de postuler.
- `ChangerStatutCandidature` — fait progresser le pipeline, avec validation des transitions.
- `AssocierDocumentUtilisé` — relie la candidature au CV/lettre généré par `cv-agent`.
- `ConsulterPipelineCandidatures` — vue filtrée par statut, pour `dashboard-agent`/`recruiter-agent`.
- `ClôturerCandidature` — refus, acceptation ou abandon.

**Entretiens**
- `PlanifierEntretien`
- `EnregistrerCompteRenduEntretien`
- `ConsulterHistoriqueEntretiens` (par candidature, pour préparer le suivant via `interview-agent`).

**Contacts**
- `AjouterContact` / `MettreÀJourContact`
- `ConsulterContactsParCandidature` / `ConsulterContactsParMission`

---

## Points à valider avant implémentation

1. **StatutCandidature** : la machine à états proposée (`Repérée → Postulée → EntretienPlanifié → EntretienRéalisé → OffreReçue → Acceptée`, avec sorties `Refusée/SansRéponse/Abandonnée`) doit être confirmée — elle reprend le pipeline mentionné dans `agents/recruiter-agent/README.md` (`repéré → postulé → entretien → offre → clos`) en le détaillant.
2. **Persistance des événements** : simple journal (append-only) ou véritable event sourcing ? Impacte le choix de stockage (Sprint suivant).
3. **Granularité de `MettreÀJourProfil`** : un seul cas d'usage générique ou un cas d'usage par type de changement (compétence, expérience, préférences) comme proposé ici ? Le second est plus explicite mais plus verbeux.
4. **Un seul `Profil`** : on part du principe mono-utilisateur (pas de multi-profil). À confirmer que ça reste vrai pour toute la durée du projet.
