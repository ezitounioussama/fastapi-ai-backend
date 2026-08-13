"""Placeholder logic for the three AI-facing endpoints.

Everything here is plain, deterministic Python — no model calls, no network, no
API key. The point is that the endpoints work and can be tested today, while the
request and response shapes are already the ones a real model would fill in.

Swapping in a real model later means rewriting these three functions and nothing
else: the routers and the Pydantic models stay as they are.

Deterministic matters for testing. Nothing here uses randomness, so the same
input always produces the same output and the tests can assert exact values.
"""

import re
from datetime import datetime, timezone
from typing import List

from app.models import QuizQuestion


def utc_now() -> datetime:
    """Current time as an aware UTC datetime.

    datetime.now(timezone.utc) rather than datetime.utcnow(): the latter returns
    a naive datetime with no timezone attached (and is deprecated in 3.12+),
    which serialises without the 'Z' and invites off-by-hours bugs.
    """
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# /chat
# ---------------------------------------------------------------------------

# Canned explanations, so common beginner questions get a sensible reply even
# with no model attached.
_CANNED_ANSWERS = {
    "list": (
        "A list stores several values in order under one name, written with "
        "square brackets: scores = [10, 20, 30]. You reach an item by its "
        "position, counting from 0, so scores[0] is 10."
    ),
    "variable": (
        "A variable is a name attached to a value so you can use it later, "
        "for example age = 25. Assigning again replaces the value."
    ),
    "function": (
        "A function is a named block of code you can run whenever you need it. "
        "You define it with def, give it inputs (parameters), and it can hand "
        "back a result with return."
    ),
    "loop": (
        "A loop repeats work. A for loop walks through the items of a "
        "collection, while a while loop keeps going until its condition stops "
        "being true."
    ),
    "dictionary": (
        "A dictionary stores key-value pairs, written with curly braces: "
        "ages = {'Sara': 25}. You look values up by key rather than position."
    ),
    "api": (
        "An API is an agreed way for two programs to talk. A web API takes a "
        "request at a URL and sends back structured data, usually JSON."
    ),
}


def generate_chat_answer(message: str) -> str:
    """Return a placeholder answer for one question.

    Looks for a known keyword in the message and returns the matching
    explanation; otherwise returns an honest "not wired up yet" reply rather
    than inventing something, which is the same rule a real model would be
    given in its system prompt.
    """
    lowered = message.lower()

    for keyword, answer in _CANNED_ANSWERS.items():
        if keyword in lowered:
            return answer

    return (
        "This endpoint is running on placeholder logic, so there is no real "
        "answer for that question yet. Known example topics: "
        + ", ".join(sorted(_CANNED_ANSWERS))
        + "."
    )


# ---------------------------------------------------------------------------
# /quiz
# ---------------------------------------------------------------------------

# Question templates. Each one becomes a question about whatever topic is asked
# for, so the endpoint returns a plausible quiz for any input.
_QUESTION_TEMPLATES = [
    (
        "Which statement best describes {topic}?",
        ["The correct description", "A wrong description", "An unrelated idea", "None of these"],
    ),
    (
        "In which situation would you use {topic}?",
        ["The appropriate situation", "A situation where it does not apply",
         "Never", "Only in other languages"],
    ),
    (
        "What is a common mistake when working with {topic}?",
        ["The usual beginner mistake", "There are no mistakes possible",
         "Using it correctly", "Reading the documentation"],
    ),
    (
        "Which of these is NOT true about {topic}?",
        ["The false statement", "A true statement", "Another true statement",
         "A third true statement"],
    ),
    (
        "How would you explain {topic} to a beginner?",
        ["A clear simple explanation", "A confusing explanation",
         "By avoiding the question", "With unrelated jargon"],
    ),
    (
        "What comes right after learning {topic}?",
        ["The natural next step", "Nothing", "An unrelated topic", "Starting over"],
    ),
    (
        "Which keyword is most associated with {topic}?",
        ["The related keyword", "An unrelated keyword", "No keyword", "All keywords"],
    ),
    (
        "What problem does {topic} solve?",
        ["The problem it addresses", "It solves nothing",
         "A different problem", "It creates problems"],
    ),
    (
        "Where would you look up more about {topic}?",
        ["The official documentation", "Nowhere", "A random guess", "Only in videos"],
    ),
    (
        "What is the main benefit of {topic}?",
        ["The main benefit", "There is no benefit", "It is slower", "It is harder"],
    ),
]


def generate_quiz(topic: str, num_questions: int) -> List[QuizQuestion]:
    """Build `num_questions` placeholder questions about `topic`.

    The correct choice is always at index 0 in the templates, so the questions
    are built with the answer in a rotating position instead — otherwise every
    answer_index would be 0 and any client could cheat by ignoring the content.

    num_questions is already limited to 1-10 by QuizRequest, and there are 10
    templates, so the modulo below never has to repeat one in practice.
    """
    questions = []

    for index in range(num_questions):
        template, options = _QUESTION_TEMPLATES[index % len(_QUESTION_TEMPLATES)]

        # Rotate the correct option into a different slot for each question.
        correct = options[0]
        distractors = list(options[1:])
        answer_index = index % 4

        shuffled = distractors[:answer_index] + [correct] + distractors[answer_index:]

        questions.append(
            QuizQuestion(
                number=index + 1,
                question=template.format(topic=topic),
                options=shuffled,
                answer_index=answer_index,
            )
        )

    return questions


# ---------------------------------------------------------------------------
# /summarise
# ---------------------------------------------------------------------------


def split_sentences(text: str) -> List[str]:
    """Split text into sentences on . ! or ? followed by whitespace.

    A regex split is not perfect — "Dr. Smith" or "3.5" will fool it — but it is
    predictable and needs no extra library, which suits placeholder logic.
    """
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def summarise_text(text: str, max_bullets: int) -> List[str]:
    """Pick the most informative sentences, keeping their original order.

    This is extractive summarising: nothing is rewritten, sentences are selected.
    Two signals decide which ones:

      * position — the first sentence usually states the subject, so it gets a
        bonus
      * length — very short sentences tend to carry little information

    The chosen sentences are then put back in the order they appeared, so the
    summary still reads in sequence rather than by score.
    """
    sentences = split_sentences(text)

    # Short text: everything is already the summary.
    if len(sentences) <= max_bullets:
        return sentences

    scored = []
    for position, sentence in enumerate(sentences):
        score = len(sentence)
        if position == 0:
            score += 100  # the opening sentence is usually the topic sentence
        scored.append((score, position, sentence))

    # Highest scores first, then restore reading order among the winners.
    best = sorted(scored, reverse=True)[:max_bullets]
    best.sort(key=lambda item: item[1])

    return [sentence for _, _, sentence in best]


def compression_ratio(original: str, bullets: List[str]) -> float:
    """How much shorter the summary is, as summary length / original length."""
    original_length = len(original)
    if original_length == 0:
        return 0.0

    summary_length = sum(len(bullet) for bullet in bullets)
    return round(summary_length / original_length, 2)
