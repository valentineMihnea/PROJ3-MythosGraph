"""Unit and property-based tests for MythosGraph traversal algorithms."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from mythos_graph.domain import (
    Entity,
    EntityCategory,
    MythologicalCycle,
    Relationship,
    RelationType,
)
from mythos_graph.engine import (
    MythosGraph,
    extract_lineage,
    filter_by_cycle,
    find_shortest_path,
)


def _entity(
    entity_id: str,
    name: str,
    category: EntityCategory = EntityCategory.OLYMPIAN,
    cycles: frozenset[MythologicalCycle] = frozenset(),
) -> Entity:
    return Entity(
        id=entity_id,
        greek_name=name,
        anglicized_name=name,
        category=category,
        cycles=cycles,
    )


def _build_sample_graph() -> MythosGraph:
    graph = MythosGraph()
    for entity in (
        _entity(
            "cronus", "Cronus", EntityCategory.TITAN, frozenset({MythologicalCycle.TITANOMACHY})
        ),
        _entity(
            "zeus", "Zeus", EntityCategory.OLYMPIAN, frozenset({MythologicalCycle.TITANOMACHY})
        ),
        _entity("heracles", "Heracles", EntityCategory.DEMIGOD),
        _entity("minos", "Minos", EntityCategory.MORTAL),
        _entity("athena", "Athena", EntityCategory.OLYMPIAN),
        _entity("isolated", "Chaos", EntityCategory.PRIMORDIAL),
    ):
        graph.add_entity(entity)

    edges = [
        Relationship(
            source_id="cronus",
            target_id="zeus",
            relation_type=RelationType.PARENT_OF,
            cycles=frozenset({MythologicalCycle.TITANOMACHY}),
            weight=1.0,
        ),
        Relationship(
            source_id="zeus",
            target_id="heracles",
            relation_type=RelationType.PARENT_OF,
            weight=5.0,
        ),
        Relationship(
            source_id="zeus",
            target_id="minos",
            relation_type=RelationType.PARENT_OF,
            weight=1.0,
        ),
        Relationship(
            source_id="zeus",
            target_id="athena",
            relation_type=RelationType.PARENT_OF,
            weight=1.0,
        ),
        Relationship(
            source_id="athena",
            target_id="heracles",
            relation_type=RelationType.PATRON_OF,
            weight=1.0,
        ),
    ]
    for edge in edges:
        graph.add_relationship(edge)
    return graph


def test_bfs_and_dijkstra_shortest_paths() -> None:
    """BFS minimizes hops while Dijkstra minimizes total edge weight."""
    graph = _build_sample_graph()

    bfs_path = find_shortest_path(graph, "zeus", "heracles", algorithm="bfs", bidirectional=False)
    assert bfs_path is not None
    assert bfs_path.hops == 1
    assert bfs_path.total_weight == 5.0

    dijkstra_path = find_shortest_path(
        graph, "zeus", "heracles", algorithm="dijkstra", bidirectional=False
    )
    assert dijkstra_path is not None
    assert dijkstra_path.hops == 2
    assert dijkstra_path.total_weight == 2.0
    assert [step.to_id for step in dijkstra_path.steps] == ["athena", "heracles"]


def test_bidirectional_kinship_path_and_unreachable() -> None:
    """Bidirectional search connects siblings through a shared parent."""
    graph = _build_sample_graph()

    path = find_shortest_path(graph, "heracles", "minos", algorithm="bfs", bidirectional=True)
    assert path is not None
    assert path.hops == 2
    assert path.steps[0].direction == "incoming"
    assert path.steps[0].to_id == "zeus"
    assert path.steps[1].direction == "outgoing"
    assert path.steps[1].to_id == "minos"

    assert find_shortest_path(graph, "heracles", "minos", bidirectional=False) is None
    assert find_shortest_path(graph, "zeus", "isolated") is None

    same = find_shortest_path(graph, "zeus", "zeus")
    assert same is not None
    assert same.hops == 0
    assert same.steps == []


def test_extract_lineage_directions_and_depth() -> None:
    """Lineage extraction respects direction, depth limit, and cycles."""
    graph = _build_sample_graph()
    # Add a CHILD_OF edge to cover both PARENT_OF and CHILD_OF lineage traversal
    graph.add_relationship(
        Relationship(
            source_id="minos",
            target_id="zeus",
            relation_type=RelationType.CHILD_OF,
        )
    )

    ancestors = extract_lineage(graph, "heracles", direction="ancestors", max_depth=2)
    assert {e.id for e in ancestors.entities} == {"heracles", "zeus", "cronus"}

    descendants = extract_lineage(graph, "cronus", direction="descendants", max_depth=1)
    assert {e.id for e in descendants.entities} == {"cronus", "zeus"}

    both = extract_lineage(graph, "zeus", direction="both", max_depth=1)
    assert {e.id for e in both.entities} == {"zeus", "cronus", "heracles", "minos", "athena"}

    with pytest.raises(ValueError, match="non-negative"):
        extract_lineage(graph, "zeus", max_depth=-1)


def test_filter_by_cycle() -> None:
    """Cycle filter returns only entities and relationships in the requested cycle."""
    graph = _build_sample_graph()
    subgraph = filter_by_cycle(graph, MythologicalCycle.TITANOMACHY)

    assert {entity.id for entity in subgraph.entities} == {"cronus", "zeus"}
    assert len(subgraph.relationships) == 1
    assert subgraph.relationships[0].source_id == "cronus"


@given(
    node_count=st.integers(min_value=2, max_value=8),
    edges=st.lists(
        st.tuples(st.integers(min_value=0, max_value=7), st.integers(min_value=0, max_value=7)),
        max_size=15,
    ),
)
def test_cyclic_graphs_terminate_and_stay_consistent(
    node_count: int,
    edges: list[tuple[int, int]],
) -> None:
    """Property test: traversal and lineage extraction terminate cleanly on cyclic graphs."""
    graph = MythosGraph()
    for idx in range(node_count):
        graph.add_entity(_entity(f"n{idx}", f"Node{idx}"))

    seen: set[tuple[int, int]] = set()
    for src, dst in edges:
        src_mod = src % node_count
        dst_mod = dst % node_count
        if src_mod == dst_mod or (src_mod, dst_mod) in seen:
            continue
        seen.add((src_mod, dst_mod))
        graph.add_relationship(
            Relationship(
                source_id=f"n{src_mod}",
                target_id=f"n{dst_mod}",
                relation_type=RelationType.PARENT_OF,
            )
        )

    lineage = extract_lineage(graph, "n0", direction="both", max_depth=node_count)
    assert len(lineage.entities) <= node_count

    path = find_shortest_path(graph, "n0", f"n{node_count - 1}", algorithm="bfs")
    if path is not None:
        assert path.hops == len(path.steps)
        assert path.hops < node_count
