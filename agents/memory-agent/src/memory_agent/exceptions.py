"""Exceptions métier du Memory Agent (docs/adr/0004-services-metier.md).

Portées par la couche Services uniquement — les repositories restent une couche
de persistance qui ne lève rien de métier (docs/domain-model.md §11).
"""


class MemoryAgentError(Exception):
    """Racine de toutes les exceptions métier du Memory Agent."""


class EntityNotFoundError(MemoryAgentError):
    def __init__(self, entity_name: str, entity_id: object) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} introuvable (id={entity_id!r})")


class DuplicateEntityError(MemoryAgentError):
    def __init__(self, entity_name: str, field: str, value: object) -> None:
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(f"{entity_name} déjà existant pour {field}={value!r}")


class InvalidStatusTransitionError(MemoryAgentError):
    def __init__(self, entity_name: str, statut_actuel: object, statut_cible: object) -> None:
        self.entity_name = entity_name
        self.statut_actuel = statut_actuel
        self.statut_cible = statut_cible
        super().__init__(f"Transition invalide pour {entity_name} : {statut_actuel} -> {statut_cible}")


class InvalidTjmRangeError(MemoryAgentError):
    def __init__(self, montant_min: float, montant_max: float) -> None:
        self.montant_min = montant_min
        self.montant_max = montant_max
        super().__init__(f"TJM min ({montant_min}) doit être <= TJM max ({montant_max})")


class InvalidPeriodError(MemoryAgentError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidQualificationError(MemoryAgentError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidMetricsStateError(MemoryAgentError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
