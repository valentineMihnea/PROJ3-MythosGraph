"""Response schemas for the MythosGraph REST API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic health check payload."""

    status: str
    version: str


class GraphStatsResponse(BaseModel):
    """Current graph node and edge totals."""

    node_count: int
    edge_count: int
