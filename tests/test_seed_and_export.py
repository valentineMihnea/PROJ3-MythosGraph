"""Tests for seed dataset loading and JGF/DOT graph serialization."""

from mythos_graph.data import load_dataset
from mythos_graph.domain import MythologicalCycle
from mythos_graph.engine import filter_by_cycle, find_shortest_path
from mythos_graph.export import to_dot, to_jgf


def test_load_hellenic_seed_and_kinship_query() -> None:
    """Seed dataset loads cleanly and answers the canonical Heracles-Minos kinship query."""
    graph = load_dataset()
    assert graph.node_count >= 20
    assert graph.edge_count >= 30

    path = find_shortest_path(graph, "heracles", "minos", algorithm="bfs")
    assert path is not None
    assert path.hops == 2
    assert path.steps[0].to_id == "zeus"
    assert path.steps[1].to_id == "minos"


def test_export_jgf_and_dot() -> None:
    """Subgraphs serialize cleanly to JGF dict and Graphviz DOT text."""
    graph = load_dataset()
    trojan = filter_by_cycle(graph, MythologicalCycle.TROJAN_WAR)

    jgf = to_jgf(trojan.entities, trojan.relationships, label="Trojan War")
    assert jgf["graph"]["directed"] is True
    assert jgf["graph"]["label"] == "Trojan War"
    assert "achilles" in jgf["graph"]["nodes"]
    assert "odysseus" in jgf["graph"]["nodes"]
    assert len(jgf["graph"]["edges"]) == len(trojan.relationships)

    dot = to_dot(trojan.entities, trojan.relationships, graph_name="TrojanWar")
    assert dot.startswith('digraph "TrojanWar" {')
    assert '"achilles" -> "odysseus" [label="ALLIED_WITH"];' in dot
    assert dot.endswith("}")
