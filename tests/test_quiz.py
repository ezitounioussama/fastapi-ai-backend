"""Tests for POST /quiz."""

from app import config


async def test_quiz_accepts_a_valid_request(client):
    response = await client.post("/quiz", json={"topic": "Python lists", "num_questions": 3})
    assert response.status_code == 200


async def test_quiz_returns_the_requested_number_of_questions(client):
    body = (await client.post("/quiz", json={"topic": "loops", "num_questions": 4})).json()

    assert body["count"] == 4
    assert len(body["questions"]) == 4


async def test_quiz_response_has_the_expected_shape(client):
    body = (await client.post("/quiz", json={"topic": "functions", "num_questions": 2})).json()

    for field in ("topic", "count", "questions", "source", "timestamp"):
        assert field in body, f"missing field: {field}"


async def test_each_question_is_fully_formed(client):
    body = (await client.post("/quiz", json={"topic": "sets", "num_questions": 5})).json()

    for position, question in enumerate(body["questions"], start=1):
        assert question["number"] == position
        assert question["question"].strip()
        assert len(question["options"]) == 4
        # The answer index must actually point at one of the options.
        assert 0 <= question["answer_index"] <= 3


async def test_the_topic_appears_in_every_question(client):
    topic = "dictionaries"
    body = (await client.post("/quiz", json={"topic": topic, "num_questions": 3})).json()

    for question in body["questions"]:
        assert topic in question["question"]


async def test_answers_are_not_always_in_the_same_slot(client):
    """If every answer_index were 0, a client could cheat without reading."""
    body = (await client.post("/quiz", json={"topic": "python", "num_questions": 8})).json()

    indexes = {question["answer_index"] for question in body["questions"]}
    assert len(indexes) > 1


async def test_num_questions_defaults_when_omitted(client):
    body = (await client.post("/quiz", json={"topic": "python"})).json()
    assert body["count"] == config.QUIZ_QUESTIONS_DEFAULT


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


async def test_quiz_rejects_zero_questions(client):
    response = await client.post("/quiz", json={"topic": "python", "num_questions": 0})
    assert response.status_code == 422


async def test_quiz_rejects_too_many_questions(client):
    response = await client.post(
        "/quiz", json={"topic": "python", "num_questions": config.QUIZ_QUESTIONS_MAX + 1}
    )
    assert response.status_code == 422


async def test_quiz_rejects_a_negative_count(client):
    response = await client.post("/quiz", json={"topic": "python", "num_questions": -3})
    assert response.status_code == 422


async def test_quiz_accepts_both_limits(client):
    """Both boundaries must be allowed, since ge/le are inclusive."""
    for count in (config.QUIZ_QUESTIONS_MIN, config.QUIZ_QUESTIONS_MAX):
        response = await client.post("/quiz", json={"topic": "python", "num_questions": count})
        assert response.status_code == 200, f"{count} should be valid"


async def test_quiz_rejects_a_topic_that_is_too_short(client):
    response = await client.post("/quiz", json={"topic": "a", "num_questions": 3})
    assert response.status_code == 422


async def test_quiz_rejects_a_missing_topic(client):
    response = await client.post("/quiz", json={"num_questions": 3})
    assert response.status_code == 422


async def test_quiz_validation_error_names_the_bad_field(client):
    body = (await client.post("/quiz", json={"topic": "python", "num_questions": 99})).json()

    fields = [item["field"] for item in body["errors"]]
    assert "body.num_questions" in fields
