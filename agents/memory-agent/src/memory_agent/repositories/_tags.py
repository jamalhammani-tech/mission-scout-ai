"""Helpers internes de persistance des tags (docs/domain-model.md §7), réutilisés par les
repositories des entités taguables. Pure mécanique de synchronisation, aucune règle métier."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from memory_agent.enums import TaggableEntityType
from memory_agent.models.tag import EntityTagModel, TagModel
from memory_agent.schemas.common import Tag


def get_tags(session: Session, entity_type: TaggableEntityType, entity_id: uuid.UUID) -> list[Tag]:
    stmt = (
        select(TagModel)
        .join(EntityTagModel, EntityTagModel.tag_id == TagModel.id)
        .where(EntityTagModel.entity_type == entity_type, EntityTagModel.entity_id == entity_id)
    )
    rows = session.execute(stmt).scalars().all()
    return [Tag(libelle=row.libelle, categorie=row.categorie) for row in rows]


def _get_or_create_tag(session: Session, tag: Tag) -> TagModel:
    stmt = select(TagModel).where(TagModel.libelle == tag.libelle, TagModel.categorie == tag.categorie)
    existing = session.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing
    created = TagModel(libelle=tag.libelle, categorie=tag.categorie)
    session.add(created)
    session.flush()
    return created


def sync_tags(
    session: Session, entity_type: TaggableEntityType, entity_id: uuid.UUID, tags: list[Tag]
) -> None:
    stmt = select(EntityTagModel).where(
        EntityTagModel.entity_type == entity_type, EntityTagModel.entity_id == entity_id
    )
    existing_links = list(session.execute(stmt).scalars().all())

    wanted_tag_models = [_get_or_create_tag(session, tag) for tag in tags]
    wanted_ids = {tm.id for tm in wanted_tag_models}

    for link in existing_links:
        if link.tag_id not in wanted_ids:
            session.delete(link)

    existing_tag_ids = {link.tag_id for link in existing_links}
    for tag_model in wanted_tag_models:
        if tag_model.id not in existing_tag_ids:
            session.add(EntityTagModel(tag_id=tag_model.id, entity_type=entity_type, entity_id=entity_id))
