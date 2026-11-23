"""Pydantic domain models for mythological entities and directed relationships."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mythos_graph.domain.enums import EntityCategory, MythologicalCycle, RelationType


class Entity(BaseModel):
    """Represents a mythological entity node in the MythosGraph."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique canonical entity identifier.")
    greek_name: str = Field(..., min_length=1, description="Canonical Greek name.")
    anglicized_name: str = Field(..., min_length=1, description="Anglicized display name.")
    category: EntityCategory = Field(..., description="Mythological entity classification.")
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value domain attributes (e.g., domain, epithet, symbol).",
    )
    attestations: list[str] = Field(
        default_factory=list,
        description="Primary classical literary attestations.",
    )
    cycles: frozenset[MythologicalCycle] = Field(
        default_factory=frozenset,
        description="Mythological cycles associated with the entity.",
    )


class Relationship(BaseModel):
    """Represents a directed, typed edge connecting two mythological entities."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    source_id: str = Field(..., min_length=1, description="Identifier of the source entity.")
    target_id: str = Field(..., min_length=1, description="Identifier of the target entity.")
    relation_type: RelationType = Field(..., description="Semantic type of the directed edge.")
    cycles: frozenset[MythologicalCycle] = Field(
        default_factory=frozenset,
        description="Mythological cycles in which this relationship occurs.",
    )
    source_text: str | None = Field(
        default=None,
        description="Optional literary citation supporting the relationship.",
    )
    weight: float = Field(
        default=1.0,
        gt=0.0,
        description="Positive traversal cost used in shortest-path queries.",
    )

    @model_validator(mode="after")
    def _reject_self_loop(self) -> "Relationship":
        """Ensure an entity cannot form a direct self-referential relationship."""
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must reference distinct entities.")
        return self
