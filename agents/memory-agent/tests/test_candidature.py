from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from memory_agent.enums import SourceType, StatutCandidature, StatutEntretien
from memory_agent.repositories.candidature import SqlAlchemyCandidatureRepository
from memory_agent.repositories.contact import SqlAlchemyContactRepository
from memory_agent.repositories.mission import SqlAlchemyMissionRepository
from memory_agent.schemas.candidature import Candidature, Entretien, HistoriqueStatutEntry
from memory_agent.schemas.common import ContactInfo, Source, Tag
from memory_agent.schemas.company import Company
from memory_agent.schemas.contact import Contact
from memory_agent.schemas.mission import Mission
from memory_agent.schemas.user import User
from tests.helpers import require_id


@pytest.fixture
def mission(session: Session, user: User, company: Company) -> Mission:
    return SqlAlchemyMissionRepository(session).sauvegarder(
        Mission(
            user_id=require_id(user),
            company_id=require_id(company),
            titre="Mission DevOps",
            source=Source(type=SourceType.LINKEDIN),
        )
    )


@pytest.fixture
def contact(session: Session, user: User, company: Company) -> Contact:
    return SqlAlchemyContactRepository(session).sauvegarder(
        Contact(
            user_id=require_id(user),
            company_id=require_id(company),
            nom="Recruteur X",
            contact_info=ContactInfo(email="recruteur@acme.com"),
            source=Source(type=SourceType.LINKEDIN),
        )
    )


def test_candidature_creation_et_recherche_par_mission(
    session: Session, user: User, mission: Mission, contact: Contact
) -> None:
    repo = SqlAlchemyCandidatureRepository(session)
    mission_id = require_id(mission)

    saved = repo.sauvegarder(
        Candidature(
            user_id=require_id(user),
            mission_id=mission_id,
            statut=StatutCandidature.POSTULEE,
            contact_ids=[require_id(contact)],
            statut_historique=[
                HistoriqueStatutEntry(
                    statut_nouveau=StatutCandidature.REPEREE, horodatage=datetime(2026, 7, 1)
                ),
                HistoriqueStatutEntry(
                    statut_precedent=StatutCandidature.REPEREE,
                    statut_nouveau=StatutCandidature.POSTULEE,
                    horodatage=datetime(2026, 7, 2),
                ),
            ],
            tags=[Tag(libelle="relance-prioritaire")],
        )
    )

    fetched = repo.par_mission(mission_id)
    assert fetched is not None
    assert fetched.id == saved.id
    assert len(fetched.statut_historique) == 2
    assert fetched.contact_ids == [require_id(contact)]
    assert fetched.tags == [Tag(libelle="relance-prioritaire")]


def test_candidature_lister_actives_exclut_les_clotures(
    session: Session, user: User, mission: Mission
) -> None:
    repo = SqlAlchemyCandidatureRepository(session)
    user_id = require_id(user)

    saved = repo.sauvegarder(
        Candidature(user_id=user_id, mission_id=require_id(mission), statut=StatutCandidature.POSTULEE)
    )
    assert saved.id in [c.id for c in repo.lister_actives(user_id)]

    saved.statut = StatutCandidature.REFUSEE
    repo.sauvegarder(saved)
    assert saved.id not in [c.id for c in repo.lister_actives(user_id)]


def test_candidature_ajout_entretien(session: Session, user: User, mission: Mission) -> None:
    repo = SqlAlchemyCandidatureRepository(session)
    saved = repo.sauvegarder(
        Candidature(
            user_id=require_id(user), mission_id=require_id(mission), statut=StatutCandidature.POSTULEE
        )
    )

    saved.entretiens.append(
        Entretien(statut=StatutEntretien.PLANIFIE, type="visio", date_prevue=datetime(2026, 7, 10))
    )
    saved.statut = StatutCandidature.ENTRETIEN_PLANIFIE
    repo.sauvegarder(saved)

    refetched = repo.par_id(require_id(saved))
    assert refetched is not None
    assert len(refetched.entretiens) == 1
    assert refetched.entretiens[0].type == "visio"
