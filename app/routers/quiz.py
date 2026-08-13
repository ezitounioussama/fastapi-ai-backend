"""POST /quiz — generate quiz questions on a topic."""

from fastapi import APIRouter, status

from app.models import ErrorResponse, QuizRequest, QuizResponse
from app.services import generate_quiz, utc_now

router = APIRouter(tags=["quiz"])


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    responses={422: {"model": ErrorResponse, "description": "Validation failed"}},
    summary="Generate a quiz",
    description=(
        "Takes a topic and a number of questions (1-10) and returns a list of "
        "multiple-choice questions, each with four options and the index of the "
        "correct one."
    ),
)
def post_quiz(request: QuizRequest) -> QuizResponse:
    questions = generate_quiz(request.topic, request.num_questions)

    return QuizResponse(
        topic=request.topic,
        count=len(questions),
        questions=questions,
        source="placeholder",
        timestamp=utc_now(),
    )
