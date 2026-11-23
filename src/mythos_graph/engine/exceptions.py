"""Domain-specific exceptions raised by the MythosGraph engine."""


class MythosGraphError(Exception):
    """Base exception for all MythosGraph engine errors."""


class EntityAlreadyExistsError(MythosGraphError):
    """Raised when attempting to insert an entity with an existing identifier."""

    def __init__(self, entity_id: str) -> None:
        super().__init__(f"Entity '{entity_id}' already exists in the graph.")
        self.entity_id = entity_id


class EntityNotFoundError(MythosGraphError):
    """Raised when a referenced entity identifier does not exist in the graph."""

    def __init__(self, entity_id: str) -> None:
        super().__init__(f"Entity '{entity_id}' was not found in the graph.")
        self.entity_id = entity_id


class DuplicateRelationshipError(MythosGraphError):
    """Raised when an identical directed relationship already exists."""

    def __init__(self, source_id: str, target_id: str, relation_type: str) -> None:
        super().__init__(
            f"Relationship ({source_id} -[{relation_type}]-> {target_id}) already exists."
        )
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type


class RelationshipNotFoundError(MythosGraphError):
    """Raised when a targeted directed relationship does not exist."""

    def __init__(self, source_id: str, target_id: str, relation_type: str) -> None:
        super().__init__(
            f"Relationship ({source_id} -[{relation_type}]-> {target_id}) was not found."
        )
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
