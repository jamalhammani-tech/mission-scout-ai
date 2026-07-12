"""Modèles SQLAlchemy 2.0 — persistance du domaine décrit dans docs/domain-model.md.

Ce module importe tous les modèles pour que `Base.metadata` (utilisé par Alembic
autogenerate) les connaisse, même si le module appelant n'importe qu'un sous-ensemble.
"""

from memory_agent.models.audit import AuditEventModel
from memory_agent.models.base import Base
from memory_agent.models.candidature import (
    CandidatureContactModel,
    CandidatureModel,
    CandidatureStatutHistoriqueModel,
    EntretienModel,
)
from memory_agent.models.company import CompanyModel
from memory_agent.models.contact import ContactModel
from memory_agent.models.document import DocumentModel
from memory_agent.models.linkedin import (
    LinkedInConversationModel,
    LinkedInMessageModel,
    LinkedInPostModel,
    LinkedInProfileModel,
)
from memory_agent.models.mission import (
    MissionCompetenceRequiseModel,
    MissionContactModel,
    MissionModel,
)
from memory_agent.models.profile import (
    ExperienceModel,
    ExperienceSkillModel,
    ProfileCompetenceModel,
    ProfileCriteriaSkillModel,
    ProfileModel,
)
from memory_agent.models.skill import SkillAliasModel, SkillModel
from memory_agent.models.tag import EntityTagModel, TagModel
from memory_agent.models.user import UserModel

__all__ = [
    "AuditEventModel",
    "Base",
    "CandidatureContactModel",
    "CandidatureModel",
    "CandidatureStatutHistoriqueModel",
    "CompanyModel",
    "ContactModel",
    "DocumentModel",
    "EntityTagModel",
    "EntretienModel",
    "ExperienceModel",
    "ExperienceSkillModel",
    "LinkedInConversationModel",
    "LinkedInMessageModel",
    "LinkedInPostModel",
    "LinkedInProfileModel",
    "MissionCompetenceRequiseModel",
    "MissionContactModel",
    "MissionModel",
    "ProfileCompetenceModel",
    "ProfileCriteriaSkillModel",
    "ProfileModel",
    "SkillAliasModel",
    "SkillModel",
    "TagModel",
    "UserModel",
]
