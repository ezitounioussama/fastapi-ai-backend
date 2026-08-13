"""Application entry point: builds the FastAPI app and attaches the routers."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import config
from app.models import ErrorResponse, ValidationErrorItem
from app.routers import chat, health, quiz, summarise

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc, the alternative renderer
)

# Each endpoint group lives in its own module under app/routers/.
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(summarise.router)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, error: RequestValidationError):
    """Return validation failures in the same object shape as everything else.

    FastAPI's default 422 body is a bare `detail` list, which is a different
    shape from every successful response here. This rewrites it into an object
    with a label, a readable message, and one entry per bad field — so a client
    can parse errors the same way it parses successes.

    The status code stays 422, which is what FastAPI and the Swagger docs
    already advertise.
    """
    items = []

    for raw in error.errors():
        # loc looks like ("body", "num_questions"); join it into a path and drop
        # the numeric indexes that appear for list items.
        location = ".".join(str(part) for part in raw["loc"])
        items.append(
            ValidationErrorItem(
                field=location,
                message=raw["msg"],
                type=raw["type"],
            )
        )

    fields = ", ".join(item.field for item in items) or "request body"

    body = ErrorResponse(
        error="validation_error",
        detail=f"The request was rejected. Check: {fields}.",
        errors=items,
    )

    return JSONResponse(
        # The literal 422 rather than a status constant: Starlette renamed
        # HTTP_422_UNPROCESSABLE_ENTITY to HTTP_422_UNPROCESSABLE_CONTENT, so
        # either name warns or breaks depending on the installed version.
        status_code=422,
        # mode="json" so the datetimes and any other rich types serialise.
        content=body.model_dump(mode="json"),
    )


@app.get("/", tags=["health"], summary="API index")
def read_root():
    """A short index, so hitting the base URL is not a 404."""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "docs": "/docs",
        "endpoints": ["/health", "/chat", "/quiz", "/summarise"],
    }
