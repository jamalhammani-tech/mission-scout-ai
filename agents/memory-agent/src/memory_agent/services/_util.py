"""Petits helpers internes partagés entre services."""

import uuid
from typing import Protocol


class _HasId(Protocol):
    id: uuid.UUID | None


def require_id(entity: _HasId) -> uuid.UUID:
    """Rétrécit `id: UUID | None` en `UUID` juste après une écriture (toujours renseigné)."""
    assert entity.id is not None
    return entity.id
