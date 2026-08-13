"""POST /summarise — shorten a block of text into bullets."""

from fastapi import APIRouter, status

from app.models import ErrorResponse, SummariseRequest, SummariseResponse
from app.services import compression_ratio, summarise_text, utc_now

router = APIRouter(tags=["summarise"])


@router.post(
    "/summarise",
    response_model=SummariseResponse,
    status_code=status.HTTP_200_OK,
    responses={422: {"model": ErrorResponse, "description": "Validation failed"}},
    summary="Summarise text",
    description=(
        "Takes a block of text and a maximum number of bullets (1-10), and "
        "returns the most informative sentences in their original order, along "
        "with before-and-after sizes."
    ),
)
def post_summarise(request: SummariseRequest) -> SummariseResponse:
    bullets = summarise_text(request.text, request.max_bullets)
    summary_characters = sum(len(bullet) for bullet in bullets)

    return SummariseResponse(
        bullets=bullets,
        bullet_count=len(bullets),
        original_characters=len(request.text),
        summary_characters=summary_characters,
        compression_ratio=compression_ratio(request.text, bullets),
        source="placeholder",
        timestamp=utc_now(),
    )
