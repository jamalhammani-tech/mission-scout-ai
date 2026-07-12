"""Vocabulaire du domaine (docs/domain-model.md) partagé entre modèles SQLAlchemy et schémas Pydantic."""

from enum import Enum


class StatutCompte(str, Enum):
    ACTIF = "actif"
    DESACTIVE = "desactive"


class CategorieSkill(str, Enum):
    LANGAGE = "langage"
    FRAMEWORK = "framework"
    CLOUD = "cloud"
    METHODE = "methode"
    SOFT_SKILL = "soft_skill"
    AUTRE = "autre"


class NiveauCompetence(str, Enum):
    JUNIOR = "junior"
    CONFIRME = "confirme"
    EXPERT = "expert"


class TypeCritereSkill(str, Enum):
    RECHERCHE = "recherche"
    EXCLU = "exclu"


class RemotePreference(str, Enum):
    TOTAL = "total"
    PARTIEL = "partiel"
    NON = "non"


class TypeContrat(str, Enum):
    FREELANCE = "freelance"
    PORTAGE = "portage"
    CDI = "cdi"


class StatutQualification(str, Enum):
    NON_QUALIFIEE = "non_qualifiee"
    QUALIFIEE = "qualifiee"
    ECARTEE = "ecartee"


class StatutCandidature(str, Enum):
    REPEREE = "reperee"
    POSTULEE = "postulee"
    ENTRETIEN_PLANIFIE = "entretien_planifie"
    ENTRETIEN_REALISE = "entretien_realise"
    OFFRE_RECUE = "offre_recue"
    ACCEPTEE = "acceptee"
    REFUSEE = "refusee"
    SANS_REPONSE = "sans_reponse"
    ABANDONNEE = "abandonnee"


class StatutEntretien(str, Enum):
    PLANIFIE = "planifie"
    REALISE = "realise"
    ANNULE = "annule"


class TypeDocument(str, Enum):
    CV = "cv"
    LETTRE_MOTIVATION = "lettre_motivation"
    PORTFOLIO = "portfolio"
    AUTRE = "autre"


class StatutPost(str, Enum):
    BROUILLON = "brouillon"
    PLANIFIE = "planifie"
    PUBLIE = "publie"
    ARCHIVE = "archive"


class StatutConversation(str, Enum):
    ACTIVE = "active"
    SANS_REPONSE = "sans_reponse"
    CLOSE = "close"


class ExpediteurMessage(str, Enum):
    UTILISATEUR = "utilisateur"
    CONTACT = "contact"


class SourceType(str, Enum):
    LINKEDIN = "linkedin"
    PLATEFORME_FREELANCE = "plateforme_freelance"
    RESEAU_PERSONNEL = "reseau_personnel"
    COOPTATION = "cooptation"
    CANDIDATURE_SPONTANEE = "candidature_spontanee"
    SAISIE_MANUELLE = "saisie_manuelle"
    GENERATION_AGENT = "generation_agent"


class ActeurType(str, Enum):
    UTILISATEUR = "utilisateur"
    AGENT = "agent"


class TaggableEntityType(str, Enum):
    MISSION = "mission"
    CANDIDATURE = "candidature"
    CONTACT = "contact"
    COMPANY = "company"
    DOCUMENT = "document"
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_CONVERSATION = "linkedin_conversation"
