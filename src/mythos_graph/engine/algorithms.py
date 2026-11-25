"""Graph traversal, kinship pathfinding, lineage extraction, and cycle filtering."""

import heapq
from collections import deque
from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mythos_graph.domain.enums import MythologicalCycle, RelationType
from mythos_graph.domain.models import Entity, Relationship
from mythos_graph.engine.graph import MythosGraph

StepDirection = Literal["outgoing", "incoming"]
PathAlgorithm = Literal["bfs", "dijkstra"]
LineageDirection = Literal["ancestors", "descendants", "both"]


class KinshipStep(BaseModel):
    """Single directed hop along a computed kinship path."""

    model_config = ConfigDict(frozen=True)

    from_id: str
    to_id: str
    relationship: Relationship
    direction: StepDirection


class KinshipPath(BaseModel):
    """Shortest kinship path between two entities."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    target_id: str
    steps: list[KinshipStep]
    total_weight: float
    hops: int


class SubgraphResult(BaseModel):
    """Extracted subgraph containing entities and their connecting relationships."""

    model_config = ConfigDict(frozen=True)

    entities: list[Entity]
    relationships: list[Relationship]


def _matches_cycle(edge: Relationship, cycle: MythologicalCycle | None) -> bool:
    return cycle is None or cycle in edge.cycles


def _iter_neighbors(
    graph: MythosGraph,
    node_id: str,
    bidirectional: bool,
    cycle: MythologicalCycle | None,
) -> Iterator[tuple[str, Relationship, StepDirection]]:
    for edge in graph.get_outgoing(node_id):
        if _matches_cycle(edge, cycle):
            yield edge.target_id, edge, "outgoing"

    if bidirectional:
        for edge in graph.get_incoming(node_id):
            if _matches_cycle(edge, cycle):
                yield edge.source_id, edge, "incoming"


def _reconstruct_path(
    source_id: str,
    target_id: str,
    came_from: dict[str, KinshipStep],
) -> KinshipPath:
    steps: list[KinshipStep] = []
    current = target_id
    while current != source_id:
        step = came_from[current]
        steps.append(step)
        current = step.from_id
    steps.reverse()

    total_weight = sum(step.relationship.weight for step in steps)
    return KinshipPath(
        source_id=source_id,
        target_id=target_id,
        steps=steps,
        total_weight=total_weight,
        hops=len(steps),
    )


def _bfs_shortest_path(
    graph: MythosGraph,
    source_id: str,
    target_id: str,
    bidirectional: bool,
    cycle: MythologicalCycle | None,
) -> KinshipPath | None:
    visited: set[str] = {source_id}
    came_from: dict[str, KinshipStep] = {}
    queue: deque[str] = deque([source_id])

    while queue:
        current = queue.popleft()
        for neighbor_id, edge, direction in _iter_neighbors(graph, current, bidirectional, cycle):
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            came_from[neighbor_id] = KinshipStep(
                from_id=current,
                to_id=neighbor_id,
                relationship=edge,
                direction=direction,
            )
            if neighbor_id == target_id:
                return _reconstruct_path(source_id, target_id, came_from)
            queue.append(neighbor_id)

    return None


def _dijkstra_shortest_path(
    graph: MythosGraph,
    source_id: str,
    target_id: str,
    bidirectional: bool,
    cycle: MythologicalCycle | None,
) -> KinshipPath | None:
    distances: dict[str, float] = {source_id: 0.0}
    came_from: dict[str, KinshipStep] = {}
    heap: list[tuple[float, str]] = [(0.0, source_id)]

    while heap:
        cost, current = heapq.heappop(heap)
        if current == target_id:
            return _reconstruct_path(source_id, target_id, came_from)
        if cost > distances[current]:
            continue

        for neighbor_id, edge, direction in _iter_neighbors(graph, current, bidirectional, cycle):
            next_cost = cost + edge.weight
            if next_cost < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = next_cost
                came_from[neighbor_id] = KinshipStep(
                    from_id=current,
                    to_id=neighbor_id,
                    relationship=edge,
                    direction=direction,
                )
                heapq.heappush(heap, (next_cost, neighbor_id))

    return None


def find_shortest_path(
    graph: MythosGraph,
    source_id: str,
    target_id: str,
    algorithm: PathAlgorithm = "bfs",
    bidirectional: bool = True,
    cycle: MythologicalCycle | None = None,
) -> KinshipPath | None:
    """Compute the shortest path between two entities using BFS or Dijkstra."""
    graph.get_entity(source_id)
    graph.get_entity(target_id)

    if source_id == target_id:
        return KinshipPath(
            source_id=source_id,
            target_id=target_id,
            steps=[],
            total_weight=0.0,
            hops=0,
        )

    if algorithm == "dijkstra":
        return _dijkstra_shortest_path(graph, source_id, target_id, bidirectional, cycle)
    return _bfs_shortest_path(graph, source_id, target_id, bidirectional, cycle)


def _descendant_edges(
    graph: MythosGraph,
    node_id: str,
    cycle: MythologicalCycle | None,
) -> Iterator[tuple[str, Relationship]]:
    for edge in graph.get_outgoing(node_id, RelationType.PARENT_OF):
        if _matches_cycle(edge, cycle):
            yield edge.target_id, edge
    for edge in graph.get_incoming(node_id, RelationType.CHILD_OF):
        if _matches_cycle(edge, cycle):
            yield edge.source_id, edge


def _ancestor_edges(
    graph: MythosGraph,
    node_id: str,
    cycle: MythologicalCycle | None,
) -> Iterator[tuple[str, Relationship]]:
    for edge in graph.get_incoming(node_id, RelationType.PARENT_OF):
        if _matches_cycle(edge, cycle):
            yield edge.source_id, edge
    for edge in graph.get_outgoing(node_id, RelationType.CHILD_OF):
        if _matches_cycle(edge, cycle):
            yield edge.target_id, edge


def _lineage_edges(
    graph: MythosGraph,
    node_id: str,
    direction: LineageDirection,
    cycle: MythologicalCycle | None,
) -> Iterator[tuple[str, Relationship]]:
    if direction in ("descendants", "both"):
        yield from _descendant_edges(graph, node_id, cycle)
    if direction in ("ancestors", "both"):
        yield from _ancestor_edges(graph, node_id, cycle)


def extract_lineage(
    graph: MythosGraph,
    root_id: str,
    direction: LineageDirection = "both",
    max_depth: int = 2,
    cycle: MythologicalCycle | None = None,
) -> SubgraphResult:
    """Extract an ancestor, descendant, or combined lineage subgraph up to max_depth."""
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative.")

    graph.get_entity(root_id)
    visited: set[str] = {root_id}
    ordered_ids: list[str] = [root_id]
    seen_edges: set[tuple[str, str, RelationType]] = set()
    collected_edges: list[Relationship] = []
    queue: deque[tuple[str, int]] = deque([(root_id, 0)])

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for neighbor_id, edge in _lineage_edges(graph, current, direction, cycle):
            edge_key = (edge.source_id, edge.target_id, edge.relation_type)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                collected_edges.append(edge)

            if neighbor_id not in visited:
                visited.add(neighbor_id)
                ordered_ids.append(neighbor_id)
                queue.append((neighbor_id, depth + 1))

    entities = [graph.get_entity(entity_id) for entity_id in ordered_ids]
    return SubgraphResult(entities=entities, relationships=collected_edges)


def filter_by_cycle(graph: MythosGraph, cycle: MythologicalCycle) -> SubgraphResult:
    """Return the subgraph of entities and relationships belonging to a mythological cycle."""
    entity_ids: set[str] = {entity.id for entity in graph.list_entities() if cycle in entity.cycles}
    relationships: list[Relationship] = []

    for entity in graph.list_entities():
        for edge in graph.get_outgoing(entity.id):
            if cycle in edge.cycles:
                relationships.append(edge)
                entity_ids.add(edge.source_id)
                entity_ids.add(edge.target_id)

    entities = [entity for entity in graph.list_entities() if entity.id in entity_ids]
    return SubgraphResult(entities=entities, relationships=relationships)
