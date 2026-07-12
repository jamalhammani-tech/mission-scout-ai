"""Vocabulaire du domaine (docs/domain-model.md) partagé entre modèles SQLAlchemy et schémas Pydantic."""

from enum import StrEnum


class StatutCompte(StrEnum):
    ACTIF = "actif"
    DESACTIVE = "desactive"


class CategorieSkill(StrEnum):
    LANGAGE = "langage"
    FRAMEWORK = "framework"
    CLOUD = "cloud"
    METHODE = "methode"
    SOFT_SKILL = "soft_skill"
    AUTRE = "autre"


class NiveauCompetence(StrEnum):
    JUNIOR = "junior"
    CONFIRME = "confirme"
    EXPERT = "expert"


class TypeCritereSkill(StrEnum):
    RECHERCHE = "recherche"
    EXCLU = "exclu"


class RemotePreference(StrEnum):
    TOTAL = "total"
    PARTIEL = "partiel"
    NON = "non"


class TypeContrat(StrEnum):
    FREELANCE = "freelance"
    PORTAGE = "portage"
    CDI = "cdi"


class StatutQualification(StrEnum):
    NON_QUALIFIEE = "non_qualifiee"
    QUALIFIEE = "qualifiee"
    ECARTEE = "ecartee"


class StatutCandidature(StrEnum):
    REPEREE = "reperee"
    POSTULEE = "postulee"
    ENTRETIEN_PLANIFIE = "entretien_planifie"
    ENTRETIEN_REALISE = "entretien_realise"
    OFFRE_RECUE = "offre_recue"
    ACCEPTEE = "acceptee"
    REFUSEE = "refusee"
    SANS_REPONSE = "sans_reponse"
    ABANDONNEE = "abandonnee"


class StatutEntretien(StrEnum):
    PLANIFIE = "planifie"
    REALISE = "realise"
    ANNULE = "annule"


class TypeDocument(StrEnum):
    CV = "cv"
    LETTRE_MOTIVATION = "lettre_motivation"
    PORTFOLIO = "portfolio"
    AUTRE = "autre"


class StatutPost(StrEnum):
    BROUILLON = "brouillon"
    PLANIFIE = "planifie"
    PUBLIE = "publie"
    ARCHIVE = "archive"


class StatutConversation(StrEnum):
    ACTIVE = "active"
    SANS_REPONSE = "sans_reponse"
    CLOSE = "close"


class ExpediteurMessage(StrEnum):
    UTILISATEUR = "utilisateur"
    CONTACT = "contact"


class SourceType(StrEnum):
    LINKEDIN = "linkedin"
    PLATEFORME_FREELANCE = "plateforme_freelance"
    RESEAU_PERSONNEL = "reseau_personnel"
    COOPTATION = "cooptation"
    CANDIDATURE_SPONTANEE = "candidature_spontanee"
    SAISIE_MANUELLE = "saisie_manuelle"
    GENERATION_AGENT = "generation_agent"


class ActeurType(StrEnum):
    UTILISATEUR = "utilisateur"
    AGENT = "agent"


class TaggableEntityType(StrEnum):
    MISSION = "mission"
    CANDIDATURE = "candidature"
    CONTACT = "contact"
    COMPANY = "company"
    DOCUMENT = "document"
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_CONVERSATION = "linkedin_conversation"
