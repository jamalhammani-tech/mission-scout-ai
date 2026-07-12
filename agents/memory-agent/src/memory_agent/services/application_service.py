import uuid
from datetime import UTC, datetime

from memory_agent.enums import StatutCandidature, StatutEntretien
from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError, InvalidStatusTransitionError
from memory_agent.repositories.interfaces import (
    AuditEventRepository,
    CandidatureRepository,
    DocumentRepository,
    MissionRepository,
)
from memory_agent.schemas.candidature import Candidature, Entretien, HistoriqueStatutEntry
from memory_agent.schemas.common import Acteur, Tag
from memory_agent.services._audit import enregistrer_evenement
from memory_agent.services._util import require_id

_TRANSITIONS: dict[StatutCandidature, frozenset[StatutCandidature]] = {
    StatutCandidature.REPEREE: frozenset({StatutCandidature.POSTULEE, StatutCandidature.ABANDONNEE}),
    StatutCandidature.POSTULEE: frozenset(
        {
            StatutCandidature.ENTRETIEN_PLANIFIE,
            StatutCandidature.REFUSEE,
            StatutCandidature.SANS_REPONSE,
            StatutCandidature.ABANDONNEE,
        }
    ),
    StatutCandidature.ENTRETIEN_PLANIFIE: frozenset(
        {
            StatutCandidature.ENTRETIEN_REALISE,
            StatutCandidature.REFUSEE,
            StatutCandidature.ABANDONNEE,
        }
    ),
    StatutCandidature.ENTRETIEN_REALISE: frozenset(
        {
            StatutCandidature.ENTRETIEN_PLANIFIE,
            StatutCandidature.OFFRE_RECUE,
            StatutCandidature.REFUSEE,
            StatutCandidature.ABANDONNEE,
        }
    ),
    StatutCandidature.OFFRE_RECUE: frozenset(
        {
            StatutCandidature.ACCEPTEE,
            StatutCandidature.REFUSEE,
            StatutCandidature.ABANDONNEE,
        }
    ),
    StatutCandidature.SANS_REPONSE: frozenset(
        {
            StatutCandidature.ENTRETIEN_PLANIFIE,
            StatutCandidature.REFUSEE,
            StatutCandidature.ABANDONNEE,
        }
    ),
    StatutCandidature.ACCEPTEE: frozenset(),
    StatutCandidature.REFUSEE: frozenset(),
    StatutCandidature.ABANDONNEE: frozenset(),
}

STATUTS_CLOTURE: frozenset[StatutCandidature] = frozenset(
    {StatutCandidature.ACCEPTEE, StatutCandidature.REFUSEE, StatutCandidature.ABANDONNEE}
)


class ApplicationService:
    """Cas d'usage de l'agrégat Candidature (docs/domain-model.md §12), y compris ses
    entités enfants Entretien — machine à états définie par `_TRANSITIONS` ci-dessus."""

    def __init__(
        self,
        candidature_repo: CandidatureRepository,
        mission_repo: MissionRepository,
        document_repo: DocumentRepository,
        audit_repo: AuditEventRepository,
    ) -> None:
        self._candidatures = candidature_repo
        self._missions = mission_repo
        self._documents = document_repo
        self._audit = audit_repo

    def creer_candidature(
        self, *, user_id: uuid.UUID, mission_id: uuid.UUID, tags: list[Tag] | None = None, acteur: Acteur
    ) -> Candidature:
        if self._missions.par_id(mission_id) is None:
            raise EntityNotFoundError("Mission", mission_id)
        if self._candidatures.par_mission(mission_id) is not None:
            raise DuplicateEntityError("Candidature", "mission_id", mission_id)

        candidature = self._candidatures.sauvegarder(
            Candidature(
                user_id=user_id,
                mission_id=mission_id,
                statut=StatutCandidature.REPEREE,
                statut_historique=[
                    HistoriqueStatutEntry(
                        statut_nouveau=StatutCandidature.REPEREE, horodatage=datetime.now(UTC)
                    )
                ],
                tags=tags or [],
            )
        )
        enregistrer_evenement(
            self._audit,
            type_evenement="CandidatureCréée",
            entite_type="Candidature",
            entite_id=require_id(candidature),
            acteur=acteur,
            proprietaire_user_id=user_id,
        )
        return candidature

    def consulter(self, candidature_id: uuid.UUID) -> Candidature:
        candidature = self._candidatures.par_id(candidature_id)
        if candidature is None:
            raise EntityNotFoundError("Candidature", candidature_id)
        return candidature

    def consulter_pipeline(
        self, user_id: uuid.UUID, *, statut: StatutCandidature | None = None
    ) -> list[Candidature]:
        if statut is not None:
            return self._candidatures.par_statut(user_id, statut)
        return self._candidatures.par_proprietaire(user_id)

    def lister_actives(self, user_id: uuid.UUID) -> list[Candidature]:
        return self._candidatures.lister_actives(user_id)

    def changer_statut(
        self,
        candidature_id: uuid.UUID,
        *,
        nouveau_statut: StatutCandidature,
        motif: str | None = None,
        acteur: Acteur,
    ) -> Candidature:
        candidature = self.consulter(candidature_id)
        self._transitionner(candidature, nouveau_statut, motif)

        saved = self._candidatures.sauvegarder(candidature)
        enregistrer_evenement(
            self._audit,
            type_evenement="StatutCandidatureChangé",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=acteur,
            proprietaire_user_id=candidature.user_id,
            details={"nouveau_statut": nouveau_statut.value, "motif": motif},
        )
        return saved

    def cloturer_candidature(
        self,
        candidature_id: uuid.UUID,
        *,
        statut: StatutCandidature,
        motif: str | None = None,
        acteur: Acteur,
    ) -> Candidature:
        if statut not in STATUTS_CLOTURE:
            raise ValueError(f"cloturer_candidature attend un statut de clôture, reçu {statut!r}")

        candidature = self.consulter(candidature_id)
        self._transitionner(candidature, statut, motif)

        saved = self._candidatures.sauvegarder(candidature)
        enregistrer_evenement(
            self._audit,
            type_evenement="CandidatureClôturée",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=acteur,
            proprietaire_user_id=candidature.user_id,
            details={"statut": statut.value, "motif": motif},
        )
        return saved

    def associer_document(
        self, candidature_id: uuid.UUID, *, document_id: uuid.UUID, acteur: Acteur
    ) -> Candidature:
        if self._documents.par_id(document_id) is None:
            raise EntityNotFoundError("Document", document_id)

        candidature = self.consulter(candidature_id)
        candidature.document_id = document_id

        saved = self._candidatures.sauvegarder(candidature)
        enregistrer_evenement(
            self._audit,
            type_evenement="DocumentAssociéÀCandidature",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=acteur,
            proprietaire_user_id=candidature.user_id,
            details={"document_id": str(document_id)},
        )
        return saved

    def planifier_entretien(
        self,
        candidature_id: uuid.UUID,
        *,
        type_entretien: str | None = None,
        date_prevue: datetime | None = None,
        acteur: Acteur,
    ) -> Candidature:
        candidature = self.consulter(candidature_id)
        self._transitionner(candidature, StatutCandidature.ENTRETIEN_PLANIFIE)
        candidature.entretiens.append(
            Entretien(statut=StatutEntretien.PLANIFIE, type=type_entretien, date_prevue=date_prevue)
        )

        saved = self._candidatures.sauvegarder(candidature)
        enregistrer_evenement(
            self._audit,
            type_evenement="EntretienPlanifié",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=acteur,
            proprietaire_user_id=candidature.user_id,
        )
        return saved

    def enregistrer_compte_rendu_entretien(
        self,
        candidature_id: uuid.UUID,
        *,
        entretien_id: uuid.UUID,
        compte_rendu: str,
        acteur: Acteur,
    ) -> Candidature:
        candidature = self.consulter(candidature_id)
        entretien = next((e for e in candidature.entretiens if e.id == entretien_id), None)
        if entretien is None:
            raise EntityNotFoundError("Entretien", entretien_id)

        entretien.statut = StatutEntretien.REALISE
        entretien.compte_rendu = compte_rendu
        entretien.date_realisee = datetime.now(UTC)
        self._transitionner(candidature, StatutCandidature.ENTRETIEN_REALISE)

        saved = self._candidatures.sauvegarder(candidature)
        enregistrer_evenement(
            self._audit,
            type_evenement="EntretienRéalisé",
            entite_type="Candidature",
            entite_id=candidature_id,
            acteur=acteur,
            proprietaire_user_id=candidature.user_id,
            details={"entretien_id": str(entretien_id)},
        )
        return saved

    def consulter_historique_entretiens(self, candidature_id: uuid.UUID) -> list[Entretien]:
        return self.consulter(candidature_id).entretiens

    @staticmethod
    def _transitionner(
        candidature: Candidature, nouveau_statut: StatutCandidature, motif: str | None = None
    ) -> None:
        statut_actuel = candidature.statut
        if nouveau_statut not in _TRANSITIONS.get(statut_actuel, frozenset()):
            raise InvalidStatusTransitionError("Candidature", statut_actuel, nouveau_statut)

        candidature.statut_historique.append(
            HistoriqueStatutEntry(
                statut_precedent=statut_actuel,
                statut_nouveau=nouveau_statut,
                horodatage=datetime.now(UTC),
                motif=motif,
            )
        )
        candidature.statut = nouveau_statut
