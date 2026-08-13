"""Tests for POST /chat."""

from app import config


async def test_chat_accepts_a_valid_message(client):
    response = await client.post("/chat", json={"message": "What is a Python list?"})
    assert response.status_code == 200


async def test_chat_returns_a_structured_answer(client):
    """The reply must be an object with named fields, not a bare string."""
    body = (await client.post("/chat", json={"message": "What is a variable?"})).json()

    assert isinstance(body, dict)
    for field in ("answer", "question", "source", "characters", "timestamp"):
        assert field in body, f"missing field: {field}"

    assert isinstance(body["answer"], str) and body["answer"]


async def test_chat_echoes_the_question(client):
    question = "What is a function?"
    body = (await client.post("/chat", json={"message": question})).json()

    assert body["question"] == question


async def test_chat_reports_placeholder_as_the_source(client):
    body = (await client.post("/chat", json={"message": "What is a loop?"})).json()
    assert body["source"] == "placeholder"


async def test_chat_character_count_matches_the_answer(client):
    body = (await client.post("/chat", json={"message": "What is a list?"})).json()
    assert body["characters"] == len(body["answer"])


async def test_chat_recognises_a_known_topic(client):
    """A known keyword should get the real explanation, not the fallback."""
    body = (await client.post("/chat", json={"message": "explain a dictionary"})).json()

    assert "key-value" in body["answer"]


async def test_chat_admits_when_it_does_not_know(client):
    """An unknown topic must say so rather than invent an answer."""
    body = (await client.post("/chat", json={"message": "quantum tunnelling"})).json()

    assert "placeholder logic" in body["answer"]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


async def test_chat_rejects_an_empty_message(client):
    response = await client.post("/chat", json={"message": ""})
    assert response.status_code == 422


async def test_chat_rejects_a_missing_message(client):
    response = await client.post("/chat", json={})
    assert response.status_code == 422


async def test_chat_rejects_a_message_over_the_limit(client):
    too_long = "a" * (config.CHAT_MESSAGE_MAX + 1)
    response = await client.post("/chat", json={"message": too_long})
    assert response.status_code == 422


async def test_chat_accepts_a_message_at_the_limit(client):
    """The boundary itself must be allowed — max_length is inclusive."""
    at_limit = "a" * config.CHAT_MESSAGE_MAX
    response = await client.post("/chat", json={"message": at_limit})
    assert response.status_code == 200


async def test_chat_rejects_a_non_string_message(client):
    response = await client.post("/chat", json={"message": 123})
    assert response.status_code == 422


async def test_validation_error_uses_the_custom_shape(client):
    """422 replies must be objects too, matching ErrorResponse."""
    body = (await client.post("/chat", json={"message": ""})).json()

    assert body["error"] == "validation_error"
    assert "detail" in body
    assert isinstance(body["errors"], list) and body["errors"]

    first = body["errors"][0]
    assert set(first) == {"field", "message", "type"}
    assert first["field"] == "body.message"
