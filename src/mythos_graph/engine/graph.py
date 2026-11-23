"""In-memory directed graph implementation using dual adjacency lists."""

from mythos_graph.domain.enums import EntityCategory, RelationType
from mythos_graph.domain.models import Entity, Relationship
from mythos_graph.engine.exceptions import (
    DuplicateRelationshipError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    RelationshipNotFoundError,
)


class MythosGraph:
    """In-memory directed multigraph storing mythological entities and relationships."""

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._outgoing: dict[str, list[Relationship]] = {}
        self._incoming: dict[str, list[Relationship]] = {}

    @property
    def node_count(self) -> int:
        """Return total number of entities currently stored in the graph."""
        return len(self._entities)

    @property
    def edge_count(self) -> int:
        """Return total number of directed relationships currently stored in the graph."""
        return sum(len(edges) for edges in self._outgoing.values())

    def _require_entity(self, entity_id: str) -> Entity:
        """Return an existing entity or raise EntityNotFoundError."""
        entity = self._entities.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity

    def add_entity(self, entity: Entity) -> Entity:
        """Insert a new entity into the graph."""
        if entity.id in self._entities:
            raise EntityAlreadyExistsError(entity.id)
        self._entities[entity.id] = entity
        self._outgoing[entity.id] = []
        self._incoming[entity.id] = []
        return entity

    def get_entity(self, entity_id: str) -> Entity:
        """Retrieve an entity by its canonical identifier."""
        return self._require_entity(entity_id)

    def update_entity(self, entity: Entity) -> Entity:
        """Replace an existing entity's data while preserving incident relationships."""
        self._require_entity(entity.id)
        self._entities[entity.id] = entity
        return entity

    def delete_entity(self, entity_id: str) -> None:
        """Remove an entity and clean up all incoming and outgoing relationships."""
        self._require_entity(entity_id)

        for edge in self._outgoing[entity_id]:
            self._incoming[edge.target_id] = [
                inc for inc in self._incoming[edge.target_id] if inc.source_id != entity_id
            ]

        for edge in self._incoming[entity_id]:
            self._outgoing[edge.source_id] = [
                out for out in self._outgoing[edge.source_id] if out.target_id != entity_id
            ]

        del self._outgoing[entity_id]
        del self._incoming[entity_id]
        del self._entities[entity_id]

    def list_entities(self, category: EntityCategory | None = None) -> list[Entity]:
        """List all entities, optionally filtered by mythological category."""
        entities = list(self._entities.values())
        if category is None:
            return entities
        return [entity for entity in entities if entity.category == category]

    def add_relationship(self, relationship: Relationship) -> Relationship:
        """Add a directed relationship between two existing entities."""
        self._require_entity(relationship.source_id)
        self._require_entity(relationship.target_id)

        existing = self._outgoing[relationship.source_id]
        if any(
            edge.target_id == relationship.target_id
            and edge.relation_type == relationship.relation_type
            for edge in existing
        ):
            raise DuplicateRelationshipError(
                relationship.source_id,
                relationship.target_id,
                relationship.relation_type.value,
            )

        existing.append(relationship)
        self._incoming[relationship.target_id].append(relationship)
        return relationship

    def get_outgoing(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Relationship]:
        """Return outgoing relationships from an entity, optionally filtered by type."""
        self._require_entity(entity_id)
        edges = list(self._outgoing[entity_id])
        if relation_type is None:
            return edges
        return [edge for edge in edges if edge.relation_type == relation_type]

    def get_incoming(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Relationship]:
        """Return incoming relationships to an entity, optionally filtered by type."""
        self._require_entity(entity_id)
        edges = list(self._incoming[entity_id])
        if relation_type is None:
            return edges
        return [edge for edge in edges if edge.relation_type == relation_type]

    def remove_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
    ) -> None:
        """Remove a specific directed relationship between two entities."""
        self._require_entity(source_id)
        self._require_entity(target_id)

        outgoing_edges = self._outgoing[source_id]
        filtered_out = [
            edge
            for edge in outgoing_edges
            if not (edge.target_id == target_id and edge.relation_type == relation_type)
        ]
        if len(filtered_out) == len(outgoing_edges):
            raise RelationshipNotFoundError(source_id, target_id, relation_type.value)

        self._outgoing[source_id] = filtered_out
        self._incoming[target_id] = [
            edge
            for edge in self._incoming[target_id]
            if not (edge.source_id == source_id and edge.relation_type == relation_type)
        ]
