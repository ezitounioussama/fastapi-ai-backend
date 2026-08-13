"""Pydantic models: the request and response shapes for every endpoint.

Requests carry validation limits so bad input is rejected by FastAPI before any
route code runs, and the limits show up automatically in the Swagger docs.

Responses are declared too, which keeps the JSON shape stable and documented.
Nothing returns a bare string — every reply is an object with named fields, so
extra fields can be added later without breaking a client.
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from app import config


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Service status. Never touches the AI layer."""

    status: Literal["ok"] = Field(description="Service state, 'ok' when running.")
    version: str = Field(description="API version.", examples=["1.0.0"])
    timestamp: datetime = Field(description="Server time in UTC when answering.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "version": "1.0.0",
                    "timestamp": "2026-08-13T10:30:00Z",
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# /chat
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """A single question for the assistant."""

    message: str = Field(
        min_length=config.CHAT_MESSAGE_MIN,
        max_length=config.CHAT_MESSAGE_MAX,
        description="The question to ask. Cannot be empty.",
        examples=["What is a Python list?"],
    )

    model_config = {
        "json_schema_extra": {"examples": [{"message": "What is a Python list?"}]}
    }


class ChatResponse(BaseModel):
    """The assistant's reply, plus context about how it was produced."""

    answer: str = Field(description="The reply text.")
    question: str = Field(description="The question this answers, echoed back.")
    source: Literal["placeholder", "model"] = Field(
        description="'placeholder' while running on stub logic."
    )
    characters: int = Field(description="Length of the answer, in characters.")
    timestamp: datetime = Field(description="When the reply was produced.")


# ---------------------------------------------------------------------------
# /quiz
# ---------------------------------------------------------------------------


class QuizQuestion(BaseModel):
    """One multiple-choice question."""

    number: int = Field(description="Position in the quiz, starting at 1.")
    question: str = Field(description="The question text.")
    options: List[str] = Field(description="Four answer choices.")
    answer_index: int = Field(
        ge=0, le=3, description="Index into options of the correct choice."
    )


class QuizRequest(BaseModel):
    """A topic and how many questions to generate."""

    topic: str = Field(
        min_length=config.QUIZ_TOPIC_MIN,
        max_length=config.QUIZ_TOPIC_MAX,
        description="What the quiz should be about.",
        examples=["Python lists"],
    )
    num_questions: int = Field(
        default=config.QUIZ_QUESTIONS_DEFAULT,
        ge=config.QUIZ_QUESTIONS_MIN,
        le=config.QUIZ_QUESTIONS_MAX,
        description=(
            f"How many questions to return "
            f"({config.QUIZ_QUESTIONS_MIN}-{config.QUIZ_QUESTIONS_MAX})."
        ),
        examples=[3],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"topic": "Python lists", "num_questions": 3}]
        }
    }


class QuizResponse(BaseModel):
    """A generated quiz."""

    topic: str = Field(description="The topic requested.")
    count: int = Field(description="How many questions were returned.")
    questions: List[QuizQuestion] = Field(description="The questions themselves.")
    source: Literal["placeholder", "model"] = Field(description="How it was produced.")
    timestamp: datetime = Field(description="When the quiz was generated.")


# ---------------------------------------------------------------------------
# /summarise
# ---------------------------------------------------------------------------


class SummariseRequest(BaseModel):
    """Text to shorten, and how many bullets to return."""

    text: str = Field(
        min_length=config.SUMMARY_TEXT_MIN,
        max_length=config.SUMMARY_TEXT_MAX,
        description=(
            f"The text to summarise "
            f"({config.SUMMARY_TEXT_MIN}-{config.SUMMARY_TEXT_MAX} characters)."
        ),
    )
    max_bullets: int = Field(
        default=config.SUMMARY_BULLETS_DEFAULT,
        ge=config.SUMMARY_BULLETS_MIN,
        le=config.SUMMARY_BULLETS_MAX,
        description=(
            f"Largest number of bullets to return "
            f"({config.SUMMARY_BULLETS_MIN}-{config.SUMMARY_BULLETS_MAX})."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": (
                        "Python is a high-level programming language. It is known "
                        "for readable syntax. Many beginners start with Python "
                        "because the code looks close to plain English. It is used "
                        "for web development, data analysis and automation."
                    ),
                    "max_bullets": 3,
                }
            ]
        }
    }


class SummariseResponse(BaseModel):
    """A short summary, with before-and-after sizes."""

    bullets: List[str] = Field(description="The summary, one point per bullet.")
    bullet_count: int = Field(description="How many bullets were returned.")
    original_characters: int = Field(description="Length of the submitted text.")
    summary_characters: int = Field(description="Length of the summary.")
    compression_ratio: float = Field(
        description="summary_characters / original_characters, rounded to 2 places."
    )
    source: Literal["placeholder", "model"] = Field(description="How it was produced.")
    timestamp: datetime = Field(description="When the summary was produced.")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ValidationErrorItem(BaseModel):
    """One thing that was wrong with a request."""

    field: str = Field(description="Which field failed, e.g. 'body.num_questions'.")
    message: str = Field(description="What was wrong with it.")
    type: str = Field(description="Pydantic's name for the rule that failed.")


class ErrorResponse(BaseModel):
    """The shape returned for a rejected request.

    FastAPI's default 422 body is a bare `detail` list. This wraps it so error
    replies are objects with named fields, like every other response here.
    """

    error: str = Field(description="Short label for the problem.")
    detail: str = Field(description="Readable explanation.")
    errors: List[ValidationErrorItem] = Field(
        default_factory=list, description="One entry per invalid field."
    )
