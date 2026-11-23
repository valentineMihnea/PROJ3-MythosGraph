# MythosGraph

**Hellenic Kinship & Mythological Relationship Engine**

MythosGraph is an in-memory directed graph engine and REST API designed to model, traverse, and export complex genealogical and relational webs from Ancient Greek mythology (Hesiodic Theogony, Homeric epics, and classical cycles).

## Key Features (Planned & Implemented)

- **Domain Modeling (FR-1, FR-2):** Typed mythological entities (`Primordial`, `Titan`, `Olympian`, `Demigod`, `Mortal`, `Creature`) and directed semantic relationships (`PARENT_OF`, `CHILD_OF`, `SPOUSE_OF`, `CONSORT_OF`, `SIBLING_OF`, `SLAYER_OF`, `PATRON_OF`, `ALLIED_WITH`).
- **In-Memory Directed Graph Engine:** Adjacency-list representation with strict validation and CRUD operations.
- **Kinship Pathfinding & Lineage Extraction (FR-3, FR-4, FR-5):** Shortest-path kinship queries (BFS / Dijkstra), cycle-safe ancestor/descendant subgraph extraction, and mythological cycle filtering *(upcoming)*.
- **Serialization & Visual Export (FR-6):** JSON Graph Format (JGF), Graphviz DOT, and SVG export *(upcoming)*.
- **OpenAPI REST Service:** FastAPI interface with Swagger UI *(upcoming)*.

## Tech Stack & Engineering Toolchain

- **Language & Validation:** Python 3.12+, Pydantic v2
- **Dependency Management:** Poetry (`poetry.lock`)
- **Quality & Static Analysis:** Ruff, Black, Mypy (`--strict`), pre-commit
- **Testing:** pytest, pytest-cov (branch coverage), Hypothesis *(upcoming)*
- **CI/CD & Packaging:** GitHub Actions, Docker *(upcoming)*

## Local Setup

```bash
# Install dependencies into a local virtual environment
poetry install

# Run quality checks
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src tests

# Run test suite with branch coverage
poetry run pytest --cov=src/mythos_graph --cov-branch --cov-report=term-missing
```

## Project Structure

```text
PROJ3-MythosGraph/
├── .github/            # CI workflows and PR templates
├── .vscode/            # Shared IDE workspace settings
├── src/mythos_graph/
│   ├── domain/         # Entities, relationships, and mythological enums
│   └── engine/         # In-memory graph core and domain exceptions
└── tests/              # Unit and property-based test suites
```

## Incremental Roadmap

- [x] **Milestone 1:** Project foundation, Poetry lockfile, strict domain models, in-memory `MythosGraph` CRUD, unit tests, and CI pipeline.
- [ ] **Milestone 2:** BFS/Dijkstra kinship pathfinding, cycle-safe lineage extraction, cycle filtering, and Hypothesis property tests.
- [ ] **Milestone 3:** Canonical Greek mythology seed dataset ingestion & graph consistency validator.
- [ ] **Milestone 4:** JGF, Graphviz DOT, and SVG exporters.
- [ ] **Milestone 5:** FastAPI REST layer with Swagger UI and MkDocs documentation.
- [ ] **Milestone 6:** Performance benchmarks, memory profiling (`tracemalloc`), security scanning (`Bandit`/`Trivy`), and multi-stage Docker packaging.
