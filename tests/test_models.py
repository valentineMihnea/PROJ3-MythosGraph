"""Unit tests for MythosGraph domain enumerations and Pydantic models."""

import pytest
from pydantic import ValidationError

from mythos_graph.domain import (
    Entity,
    EntityCategory,
    MythologicalCycle,
    Relationship,
    RelationType,
)


def test_entity_creation_and_defaults() -> None:
    """Verify entity instantiation strips whitespace and sets expected defaults."""
    zeus = Entity(
        id="zeus",
        greek_name=" Ζεύς ",
        anglicized_name=" Zeus ",
        category=EntityCategory.OLYMPIAN,
        attributes={"domain": "sky"},
        attestations=["Hesiod, Theogony"],
        cycles=frozenset({MythologicalCycle.TITANOMACHY}),
    )

    assert zeus.id == "zeus"
    assert zeus.greek_name == "Ζεύς"
    assert zeus.anglicized_name == "Zeus"
    assert zeus.category is EntityCategory.OLYMPIAN
    assert zeus.attributes == {"domain": "sky"}
    assert zeus.attestations == ["Hesiod, Theogony"]
    assert MythologicalCycle.TITANOMACHY in zeus.cycles


def test_entity_rejects_empty_required_fields() -> None:
    """Verify blank identifiers or names fail validation."""
    with pytest.raises(ValidationError):
        Entity(
            id="   ",
            greek_name="Ζεύς",
            anglicized_name="Zeus",
            category=EntityCategory.OLYMPIAN,
        )


def test_relationship_rejects_self_loop() -> None:
    """Verify a relationship cannot connect an entity to itself."""
    with pytest.raises(ValidationError, match="distinct entities"):
        Relationship(
            source_id="zeus",
            target_id="zeus",
            relation_type=RelationType.PARENT_OF,
        )


def test_relationship_rejects_non_positive_weight() -> None:
    """Verify relationship traversal weight must be strictly positive."""
    with pytest.raises(ValidationError):
        Relationship(
            source_id="zeus",
            target_id="athena",
            relation_type=RelationType.PARENT_OF,
            weight=0.0,
        )
