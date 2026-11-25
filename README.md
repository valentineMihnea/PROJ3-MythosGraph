# MythosGraph

In-memory directed graph engine and REST prototype for querying Greek mythology genealogies and relationships.

See [docs/design.md](docs/design.md) for the minimal system architecture, diagrams, and endpoint overview.

## Setup

Requires Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

## Running the Prototype

The API loads a seed dataset of 20 Greek mythological figures and 31 relationships on startup:

```bash
poetry run uvicorn mythos_graph.api.app:app --reload
```

- **Web Interface (SVG Graph Explorer):** `http://127.0.0.1:8000/`
- **Interactive OpenAPI Docs (Swagger UI):** `http://127.0.0.1:8000/docs`

### Example Queries

```bash
# Shortest kinship path between Heracles and Minos (BFS)
curl "http://127.0.0.1:8000/kinship/path?source_id=heracles&target_id=minos"

# Zeus's descendants up to depth 2
curl "http://127.0.0.1:8000/entities/zeus/lineage?direction=descendants&depth=2"

# Trojan War subgraph
curl "http://127.0.0.1:8000/cycles/TROJAN_WAR"

# Export graph in Graphviz DOT or JSON Graph Format (JGF)
curl "http://127.0.0.1:8000/export/dot?cycle=TROJAN_WAR"
curl "http://127.0.0.1:8000/export/jgf?cycle=TITANOMACHY"
```

## Quality Checks & Tests

```bash
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src tests
poetry run pytest --cov=src/mythos_graph --cov-branch --cov-report=term-missing
```

## Project Layout

```text
PROJ3-MythosGraph/
├── docs/design.md           # Minimal architecture and Mermaid diagrams
├── src/mythos_graph/
│   ├── domain/              # Entity, Relationship, enums
│   ├── engine/              # MythosGraph CRUD, BFS/Dijkstra, lineage, cycle filter
│   ├── data/                # Hellenic seed JSON and loader
│   ├── export/              # JGF and Graphviz DOT serializers
│   └── api/                 # FastAPI app and response schemas
└── tests/                   # Unit, Hypothesis property, and API integration tests
```
