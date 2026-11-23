"""Unit tests for MythosGraph in-memory entity and relationship CRUD operations."""

import pytest

from mythos_graph.domain import (
    Entity,
    EntityCategory,
    MythologicalCycle,
    Relationship,
    RelationType,
)
from mythos_graph.engine import (
    DuplicateRelationshipError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    MythosGraph,
    RelationshipNotFoundError,
)


def _make_entity(
    entity_id: str,
    greek_name: str,
    anglicized_name: str,
    category: EntityCategory,
) -> Entity:
    return Entity(
        id=entity_id,
        greek_name=greek_name,
        anglicized_name=anglicized_name,
        category=category,
    )


def test_entity_crud_lifecycle() -> None:
    """Verify adding, fetching, updating, listing, and deleting entities."""
    graph = MythosGraph()
    cronus = _make_entity("cronus", "Κρόνος", "Cronus", EntityCategory.TITAN)
    zeus = _make_entity("zeus", "Ζεύς", "Zeus", EntityCategory.OLYMPIAN)

    graph.add_entity(cronus)
    graph.add_entity(zeus)

    assert graph.node_count == 2
    assert graph.get_entity("cronus") == cronus
    assert graph.list_entities() == [cronus, zeus]
    assert graph.list_entities(category=EntityCategory.OLYMPIAN) == [zeus]

    updated_zeus = zeus.model_copy(update={"attributes": {"symbol": "thunderbolt"}})
    graph.update_entity(updated_zeus)
    assert graph.get_entity("zeus").attributes == {"symbol": "thunderbolt"}

    graph.delete_entity("cronus")
    assert graph.node_count == 1
    assert graph.list_entities() == [updated_zeus]


def test_entity_duplicate_and_missing_errors() -> None:
    """Verify duplicate and missing entity operations raise domain exceptions."""
    graph = MythosGraph()
    athena = _make_entity("athena", "Ἀθηνᾶ", "Athena", EntityCategory.OLYMPIAN)
    graph.add_entity(athena)

    with pytest.raises(EntityAlreadyExistsError):
        graph.add_entity(athena)

    with pytest.raises(EntityNotFoundError):
        graph.get_entity("hades")

    with pytest.raises(EntityNotFoundError):
        graph.delete_entity("hades")


def test_relationship_crud_and_filtering() -> None:
    """Verify adding, querying, and removing typed directed relationships."""
    graph = MythosGraph()
    zeus = _make_entity("zeus", "Ζεύς", "Zeus", EntityCategory.OLYMPIAN)
    heracles = _make_entity("heracles", "Ἡρακλῆς", "Heracles", EntityCategory.DEMIGOD)
    athena = _make_entity("athena", "Ἀθηνᾶ", "Athena", EntityCategory.OLYMPIAN)

    for entity in (zeus, heracles, athena):
        graph.add_entity(entity)

    parent_edge = Relationship(
        source_id="zeus",
        target_id="heracles",
        relation_type=RelationType.PARENT_OF,
        cycles=frozenset({MythologicalCycle.GENERAL}),
        source_text="Pseudo-Apollodorus, Bibliotheca 2.4.8",
    )
    patron_edge = Relationship(
        source_id="athena",
        target_id="heracles",
        relation_type=RelationType.PATRON_OF,
    )

    graph.add_relationship(parent_edge)
    graph.add_relationship(patron_edge)

    assert graph.edge_count == 2
    assert graph.get_outgoing("zeus") == [parent_edge]
    assert graph.get_outgoing("zeus", RelationType.PARENT_OF) == [parent_edge]
    assert graph.get_outgoing("zeus", RelationType.SLAYER_OF) == []
    assert graph.get_incoming("heracles") == [parent_edge, patron_edge]
    assert graph.get_incoming("heracles", RelationType.PATRON_OF) == [patron_edge]

    graph.remove_relationship("athena", "heracles", RelationType.PATRON_OF)
    assert graph.edge_count == 1
    assert graph.get_incoming("heracles") == [parent_edge]


def test_delete_entity_cascades_incident_relationships() -> None:
    """Verify deleting a node cleans up both incoming and outgoing edges on neighbors."""
    graph = MythosGraph()
    cronus = _make_entity("cronus", "Κρόνος", "Cronus", EntityCategory.TITAN)
    zeus = _make_entity("zeus", "Ζεύς", "Zeus", EntityCategory.OLYMPIAN)
    athena = _make_entity("athena", "Ἀθηνᾶ", "Athena", EntityCategory.OLYMPIAN)

    for entity in (cronus, zeus, athena):
        graph.add_entity(entity)

    graph.add_relationship(
        Relationship(source_id="cronus", target_id="zeus", relation_type=RelationType.PARENT_OF)
    )
    graph.add_relationship(
        Relationship(source_id="zeus", target_id="athena", relation_type=RelationType.PARENT_OF)
    )
    assert graph.edge_count == 2

    graph.delete_entity("zeus")
    assert graph.node_count == 2
    assert graph.edge_count == 0
    assert graph.get_outgoing("cronus") == []
    assert graph.get_incoming("athena") == []


def test_relationship_error_cases() -> None:
    """Verify duplicate and missing relationship operations raise domain exceptions."""
    graph = MythosGraph()
    zeus = _make_entity("zeus", "Ζεύς", "Zeus", EntityCategory.OLYMPIAN)
    athena = _make_entity("athena", "Ἀθηνᾶ", "Athena", EntityCategory.OLYMPIAN)
    graph.add_entity(zeus)
    graph.add_entity(athena)

    edge = Relationship(
        source_id="zeus",
        target_id="athena",
        relation_type=RelationType.PARENT_OF,
    )
    graph.add_relationship(edge)

    with pytest.raises(DuplicateRelationshipError):
        graph.add_relationship(edge)

    with pytest.raises(RelationshipNotFoundError):
        graph.remove_relationship("zeus", "athena", RelationType.ALLIED_WITH)

    with pytest.raises(EntityNotFoundError):
        graph.add_relationship(
            Relationship(
                source_id="zeus",
                target_id="unknown",
                relation_type=RelationType.ALLIED_WITH,
            )
        )
