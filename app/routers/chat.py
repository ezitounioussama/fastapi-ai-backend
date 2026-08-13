"""POST /chat — ask the assistant a question."""

from fastapi import APIRouter, status

from app.models import ChatRequest, ChatResponse, ErrorResponse
from app.services import generate_chat_answer, utc_now

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    responses={422: {"model": ErrorResponse, "description": "Validation failed"}},
    summary="Ask a question",
    description=(
        "Takes a message and returns a structured answer. Currently backed by "
        "placeholder logic, so `source` is `placeholder`."
    ),
)
def post_chat(request: ChatRequest) -> ChatResponse:
    answer = generate_chat_answer(request.message)

    return ChatResponse(
        answer=answer,
        question=request.message,
        source="placeholder",
        characters=len(answer),
        timestamp=utc_now(),
    )
