"""FastAPI application exposing the MythosGraph prototype endpoints."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from mythos_graph import __version__
from mythos_graph.api.schemas import GraphStatsResponse, HealthResponse
from mythos_graph.data import load_dataset
from mythos_graph.domain import Entity, EntityCategory, MythologicalCycle, Relationship
from mythos_graph.engine import (
    DuplicateRelationshipError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    KinshipPath,
    LineageDirection,
    MythosGraph,
    PathAlgorithm,
    SubgraphResult,
    extract_lineage,
    filter_by_cycle,
    find_shortest_path,
)
from mythos_graph.export import to_dot, to_jgf


def _subgraph_for_export(graph: MythosGraph, cycle: MythologicalCycle | None) -> SubgraphResult:
    if cycle is not None:
        return filter_by_cycle(graph, cycle)

    entities = graph.list_entities()
    relationships: list[Relationship] = []
    for entity in entities:
        relationships.extend(graph.get_outgoing(entity.id))
    return SubgraphResult(entities=entities, relationships=relationships)


def _register_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(EntityNotFoundError)
    async def _not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @application.exception_handler(EntityAlreadyExistsError)
    @application.exception_handler(DuplicateRelationshipError)
    async def _conflict_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def _register_crud_routes(application: FastAPI, graph: MythosGraph) -> None:
    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @application.get("/stats", response_model=GraphStatsResponse, tags=["system"])
    def stats() -> GraphStatsResponse:
        return GraphStatsResponse(node_count=graph.node_count, edge_count=graph.edge_count)

    @application.get("/entities", response_model=list[Entity], tags=["entities"])
    def list_entities(category: EntityCategory | None = None) -> list[Entity]:
        return graph.list_entities(category=category)

    @application.post(
        "/entities",
        response_model=Entity,
        status_code=status.HTTP_201_CREATED,
        tags=["entities"],
    )
    def create_entity(entity: Entity) -> Entity:
        return graph.add_entity(entity)

    @application.get("/entities/{entity_id}", response_model=Entity, tags=["entities"])
    def get_entity(entity_id: str) -> Entity:
        return graph.get_entity(entity_id)

    @application.delete(
        "/entities/{entity_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["entities"],
    )
    def delete_entity(entity_id: str) -> Response:
        graph.delete_entity(entity_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.post(
        "/relationships",
        response_model=Relationship,
        status_code=status.HTTP_201_CREATED,
        tags=["relationships"],
    )
    def create_relationship(relationship: Relationship) -> Relationship:
        return graph.add_relationship(relationship)


def _register_query_routes(application: FastAPI, graph: MythosGraph) -> None:
    @application.get("/kinship/path", response_model=KinshipPath, tags=["queries"])
    def kinship_path(
        source_id: str,
        target_id: str,
        algorithm: PathAlgorithm = "bfs",
        bidirectional: bool = True,
        cycle: MythologicalCycle | None = None,
    ) -> KinshipPath:
        path = find_shortest_path(
            graph,
            source_id=source_id,
            target_id=target_id,
            algorithm=algorithm,
            bidirectional=bidirectional,
            cycle=cycle,
        )
        if path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No kinship path found between '{source_id}' and '{target_id}'.",
            )
        return path

    @application.get(
        "/entities/{entity_id}/lineage",
        response_model=SubgraphResult,
        tags=["queries"],
    )
    def entity_lineage(
        entity_id: str,
        direction: LineageDirection = "both",
        depth: int = Query(default=2, ge=0, le=10),
        cycle: MythologicalCycle | None = None,
    ) -> SubgraphResult:
        return extract_lineage(
            graph,
            root_id=entity_id,
            direction=direction,
            max_depth=depth,
            cycle=cycle,
        )

    @application.get("/cycles/{cycle}", response_model=SubgraphResult, tags=["queries"])
    def cycle_subgraph(cycle: MythologicalCycle) -> SubgraphResult:
        return filter_by_cycle(graph, cycle)

    @application.get("/export/jgf", tags=["export"])
    def export_jgf(cycle: MythologicalCycle | None = None) -> dict[str, Any]:
        subgraph = _subgraph_for_export(graph, cycle)
        label = cycle.value if cycle is not None else "MythosGraph"
        return to_jgf(subgraph.entities, subgraph.relationships, label=label)

    @application.get("/", include_in_schema=False)
    def web_ui() -> FileResponse:
        return FileResponse(Path(__file__).with_name("static") / "index.html")

    @application.get("/export/dot", response_class=PlainTextResponse, tags=["export"])
    def export_dot(cycle: MythologicalCycle | None = None) -> PlainTextResponse:
        subgraph = _subgraph_for_export(graph, cycle)
        name = cycle.value if cycle is not None else "MythosGraph"
        dot_source = to_dot(subgraph.entities, subgraph.relationships, graph_name=name)
        return PlainTextResponse(content=dot_source, media_type="text/vnd.graphviz")


def create_app(graph: MythosGraph | None = None) -> FastAPI:
    """Create and configure a FastAPI application backed by MythosGraph."""
    active_graph = graph if graph is not None else load_dataset()
    application = FastAPI(
        title="MythosGraph API",
        version=__version__,
        description="Hellenic Kinship & Mythological Relationship Engine (Prototype).",
    )
    _register_error_handlers(application)
    _register_crud_routes(application, active_graph)
    _register_query_routes(application, active_graph)
    return application


app = create_app()
