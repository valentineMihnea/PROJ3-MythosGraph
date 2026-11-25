"""Integration tests for the MythosGraph FastAPI prototype."""

from fastapi.testclient import TestClient

from mythos_graph.api import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_health_and_stats() -> None:
    """Health and stats endpoints reflect the preloaded Hellenic seed dataset."""
    client = _client()

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["node_count"] >= 20
    assert stats.json()["edge_count"] >= 30


def test_entity_and_relationship_crud_endpoints() -> None:
    """Entities and relationships can be created, fetched, and deleted over HTTP."""
    client = _client()

    new_entity = {
        "id": "orpheus",
        "greek_name": "Ὀρφεύς",
        "anglicized_name": "Orpheus",
        "category": "MORTAL",
        "attributes": {"role": "musician"},
        "attestations": ["Apollonius of Rhodes, Argonautica"],
        "cycles": ["ARGONAUTIC_EXPEDITION"],
    }
    created = client.post("/entities", json=new_entity)
    assert created.status_code == 201
    assert created.json()["id"] == "orpheus"

    duplicate = client.post("/entities", json=new_entity)
    assert duplicate.status_code == 409

    fetched = client.get("/entities/orpheus")
    assert fetched.status_code == 200
    assert fetched.json()["anglicized_name"] == "Orpheus"

    rel = client.post(
        "/relationships",
        json={
            "source_id": "apollo",
            "target_id": "orpheus",
            "relation_type": "PATRON_OF",
            "cycles": ["ARGONAUTIC_EXPEDITION"],
        },
    )
    assert rel.status_code == 201

    deleted = client.delete("/entities/orpheus")
    assert deleted.status_code == 204
    assert client.get("/entities/orpheus").status_code == 404


def test_kinship_lineage_cycle_and_export_endpoints() -> None:
    """Kinship pathfinding, lineage extraction, cycle filtering, and exports work end-to-end."""
    client = _client()

    path_resp = client.get("/kinship/path", params={"source_id": "heracles", "target_id": "minos"})
    assert path_resp.status_code == 200
    assert path_resp.json()["hops"] == 2

    missing_path = client.get(
        "/kinship/path",
        params={"source_id": "heracles", "target_id": "minos", "bidirectional": False},
    )
    assert missing_path.status_code == 404

    lineage = client.get(
        "/entities/zeus/lineage",
        params={"direction": "descendants", "depth": 1},
    )
    assert lineage.status_code == 200
    entity_ids = {item["id"] for item in lineage.json()["entities"]}
    assert {"zeus", "heracles", "minos", "athena"}.issubset(entity_ids)

    cycle = client.get("/cycles/TROJAN_WAR")
    assert cycle.status_code == 200
    assert any(item["id"] == "achilles" for item in cycle.json()["entities"])

    jgf = client.get("/export/jgf", params={"cycle": "TROJAN_WAR"})
    assert jgf.status_code == 200
    assert jgf.json()["graph"]["directed"] is True

    dot = client.get("/export/dot")
    assert dot.status_code == 200
    assert dot.text.startswith('digraph "MythosGraph" {')
