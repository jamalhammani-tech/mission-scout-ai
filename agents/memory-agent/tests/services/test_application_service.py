import uuid

import pytest

from memory_agent.enums import SourceType, StatutCandidature, StatutEntretien, TypeDocument
from memory_agent.exceptions import DuplicateEntityError, EntityNotFoundError, InvalidStatusTransitionError
from memory_agent.repositories.audit import SqlAlchemyAuditEventRepository
from memory_agent.repositories.candidature import SqlAlchemyCandidatureRepository
from memory_agent.repositories.document import SqlAlchemyDocumentRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.schemas.common import Acteur, Source
from memory_agent.schemas.company import Company
from memory_agent.schemas.document import Document
from memory_agent.schemas.mission import Mission
from memory_agent.schemas.user import User
from memory_agent.services.application_service import ApplicationService
from tests.helpers import require_id


@pytest.fixture
def service(
    candidature_repo: SqlAlchemyCandidatureRepository,
    mission_repo: SqlAlchemyMissionRepository,
    document_repo: SqlAlchemyDocumentRepository,
    audit_repo: SqlAlchemyAuditEventRepository,
) -> ApplicationService:
    return ApplicationService(candidature_repo, mission_repo, document_repo, audit_repo)


@pytest.fixture
def mission(mission_repo: SqlAlchemyMissionRepository, user: User, company: Company) -> Mission:
    return mission_repo.sauvegarder(
        Mission(
            user_id=require_id(user),
            company_id=require_id(company),
            titre="Mission DevOps",
            source=Source(type=SourceType.LINKEDIN),
        )
    )


def test_creer_candidature_mission_inconnue_leve_not_found(
    service: ApplicationService, user: User, acteur: Acteur
) -> None:
    with pytest.raises(EntityNotFoundError):
        service.creer_candidature(user_id=require_id(user), mission_id=uuid.uuid4(), acteur=acteur)


def test_creer_candidature(service: ApplicationService, user: User, mission: Mission, acteur: Acteur) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )

    assert candidature.statut == StatutCandidature.REPEREE
    assert len(candidature.statut_historique) == 1


def test_creer_candidature_en_double_leve_duplicate(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    service.creer_candidature(user_id=require_id(user), mission_id=require_id(mission), acteur=acteur)
    with pytest.raises(DuplicateEntityError):
        service.creer_candidature(user_id=require_id(user), mission_id=require_id(mission), acteur=acteur)


def test_changer_statut_transition_valide(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )

    postulee = service.changer_statut(
        require_id(candidature), nouveau_statut=StatutCandidature.POSTULEE, acteur=acteur
    )

    assert postulee.statut == StatutCandidature.POSTULEE
    assert len(postulee.statut_historique) == 2


def test_changer_statut_transition_invalide_leve_erreur(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )

    with pytest.raises(InvalidStatusTransitionError):
        service.changer_statut(
            require_id(candidature), nouveau_statut=StatutCandidature.ACCEPTEE, acteur=acteur
        )


def test_cloturer_candidature_statut_invalide_leve_value_error(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )

    with pytest.raises(ValueError, match="clôture"):
        service.cloturer_candidature(
            require_id(candidature), statut=StatutCandidature.POSTULEE, acteur=acteur
        )


def test_cloturer_candidature(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )
    service.changer_statut(require_id(candidature), nouveau_statut=StatutCandidature.POSTULEE, acteur=acteur)

    cloturee = service.cloturer_candidature(
        require_id(candidature), statut=StatutCandidature.REFUSEE, motif="pas retenu", acteur=acteur
    )

    assert cloturee.statut == StatutCandidature.REFUSEE
    assert cloturee.id not in [c.id for c in service.lister_actives(require_id(user))]


def test_associer_document_inconnu_leve_not_found(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )
    with pytest.raises(EntityNotFoundError):
        service.associer_document(require_id(candidature), document_id=uuid.uuid4(), acteur=acteur)


def test_associer_document(
    service: ApplicationService,
    document_repo: SqlAlchemyDocumentRepository,
    user: User,
    mission: Mission,
    acteur: Acteur,
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )
    document = document_repo.sauvegarder(
        Document(
            user_id=require_id(user),
            type=TypeDocument.CV,
            reference_fichier="data/cv.pdf",
            source=Source(type=SourceType.GENERATION_AGENT),
        )
    )

    updated = service.associer_document(
        require_id(candidature), document_id=require_id(document), acteur=acteur
    )
    assert updated.document_id == require_id(document)


def test_planifier_puis_realiser_entretien(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )
    service.changer_statut(require_id(candidature), nouveau_statut=StatutCandidature.POSTULEE, acteur=acteur)

    planifiee = service.planifier_entretien(require_id(candidature), type_entretien="visio", acteur=acteur)
    assert planifiee.statut == StatutCandidature.ENTRETIEN_PLANIFIE
    assert len(planifiee.entretiens) == 1

    entretien_id = planifiee.entretiens[0].id
    assert entretien_id is not None

    realisee = service.enregistrer_compte_rendu_entretien(
        require_id(candidature), entretien_id=entretien_id, compte_rendu="bon feeling", acteur=acteur
    )
    assert realisee.statut == StatutCandidature.ENTRETIEN_REALISE
    assert realisee.entretiens[0].statut == StatutEntretien.REALISE
    assert realisee.entretiens[0].compte_rendu == "bon feeling"


def test_enregistrer_compte_rendu_entretien_inconnu_leve_not_found(
    service: ApplicationService, user: User, mission: Mission, acteur: Acteur
) -> None:
    candidature = service.creer_candidature(
        user_id=require_id(user), mission_id=require_id(mission), acteur=acteur
    )
    service.changer_statut(require_id(candidature), nouveau_statut=StatutCandidature.POSTULEE, acteur=acteur)
    service.planifier_entretien(require_id(candidature), acteur=acteur)

    with pytest.raises(EntityNotFoundError):
        service.enregistrer_compte_rendu_entretien(
            require_id(candidature), entretien_id=uuid.uuid4(), compte_rendu="x", acteur=acteur
        )
