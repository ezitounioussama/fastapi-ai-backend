"""GET /health — service status.

Deliberately does not touch app.services beyond reading the clock, so it stays
usable as a liveness check even if the AI layer is broken or unreachable.
"""

from fastapi import APIRouter

from app import config
from app.models import HealthResponse
from app.services import utc_now

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the service status, the API version and the current UTC "
        "timestamp. This endpoint never calls the AI layer, so it answers even "
        "when the model is unavailable."
    ),
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=config.APP_VERSION,
        timestamp=utc_now(),
    )
