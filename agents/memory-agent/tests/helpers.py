import uuid
from typing import Protocol


class _HasId(Protocol):
    id: uuid.UUID | None


def require_id(entity: _HasId) -> uuid.UUID:
    """Rétrécit `id: UUID | None` en `UUID` pour une entité déjà persistée (schémas §5 domain-model.md)."""
    assert entity.id is not None
    return entity.id
