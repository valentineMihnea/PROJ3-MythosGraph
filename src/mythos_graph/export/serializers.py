"""Serializers converting MythosGraph subgraphs to JGF and Graphviz DOT."""

from collections.abc import Sequence
from typing import Any

from mythos_graph.domain import Entity, Relationship


def _escape_dot(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_jgf(
    entities: Sequence[Entity],
    relationships: Sequence[Relationship],
    label: str = "MythosGraph",
) -> dict[str, Any]:
    """Serialize entities and relationships into JSON Graph Format (JGF)."""
    nodes: dict[str, dict[str, Any]] = {
        entity.id: {
            "label": entity.anglicized_name,
            "metadata": {
                "greek_name": entity.greek_name,
                "category": entity.category.value,
                "attributes": entity.attributes,
                "attestations": entity.attestations,
                "cycles": sorted(cycle.value for cycle in entity.cycles),
            },
        }
        for entity in entities
    }

    edges: list[dict[str, Any]] = [
        {
            "source": rel.source_id,
            "target": rel.target_id,
            "relation": rel.relation_type.value,
            "metadata": {
                "weight": rel.weight,
                "source_text": rel.source_text,
                "cycles": sorted(cycle.value for cycle in rel.cycles),
            },
        }
        for rel in relationships
    ]

    return {
        "graph": {
            "directed": True,
            "label": label,
            "nodes": nodes,
            "edges": edges,
        }
    }


def to_dot(
    entities: Sequence[Entity],
    relationships: Sequence[Relationship],
    graph_name: str = "MythosGraph",
) -> str:
    """Serialize entities and relationships into a Graphviz DOT digraph string."""
    lines: list[str] = [f'digraph "{_escape_dot(graph_name)}" {{']
    lines.append("  rankdir=TB;")

    for entity in entities:
        node_label = f"{entity.anglicized_name}\\n({entity.category.value})"
        lines.append(f'  "{_escape_dot(entity.id)}" [label="{_escape_dot(node_label)}"];')

    for rel in relationships:
        lines.append(
            f'  "{_escape_dot(rel.source_id)}" -> "{_escape_dot(rel.target_id)}" '
            f'[label="{_escape_dot(rel.relation_type.value)}"];'
        )

    lines.append("}")
    return "\n".join(lines)
