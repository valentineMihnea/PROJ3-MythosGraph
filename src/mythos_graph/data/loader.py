"""JSON dataset loader that populates a MythosGraph instance."""

import json
from pathlib import Path
from typing import Any

from mythos_graph.domain import Entity, Relationship
from mythos_graph.engine import MythosGraph

DEFAULT_SEED_PATH = Path(__file__).with_name("hellenic_seed.json")


def load_dataset(path: Path | None = None) -> MythosGraph:
    """Load entities and relationships from a JSON file into a new MythosGraph."""
    dataset_path = path or DEFAULT_SEED_PATH
    raw_data: dict[str, Any] = json.loads(dataset_path.read_text(encoding="utf-8"))

    graph = MythosGraph()
    for entity_payload in raw_data.get("entities", []):
        graph.add_entity(Entity.model_validate(entity_payload))

    for rel_payload in raw_data.get("relationships", []):
        graph.add_relationship(Relationship.model_validate(rel_payload))

    return graph
