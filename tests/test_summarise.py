"""Tests for POST /summarise."""

from app import config

SAMPLE = (
    "Python is a high-level programming language. It is known for readable syntax. "
    "Many beginners start with Python because the code looks close to plain English. "
    "It is widely used for web development, data analysis and automation. "
    "The standard library covers a very large range of tasks."
)


async def test_summarise_accepts_a_valid_request(client):
    response = await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 3})
    assert response.status_code == 200


async def test_response_has_the_expected_shape(client):
    body = (await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 3})).json()

    for field in (
        "bullets",
        "bullet_count",
        "original_characters",
        "summary_characters",
        "compression_ratio",
        "source",
        "timestamp",
    ):
        assert field in body, f"missing field: {field}"


async def test_bullets_never_exceed_the_maximum(client):
    for maximum in (1, 2, 3, 4):
        body = (await client.post(
            "/summarise", json={"text": SAMPLE, "max_bullets": maximum}
        )).json()

        assert body["bullet_count"] <= maximum
        assert len(body["bullets"]) == body["bullet_count"]


async def test_the_summary_is_shorter_than_the_original(client):
    body = (await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 2})).json()

    assert body["summary_characters"] < body["original_characters"]
    assert 0 < body["compression_ratio"] < 1


async def test_original_character_count_is_accurate(client):
    body = (await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 3})).json()
    assert body["original_characters"] == len(SAMPLE)


async def test_every_bullet_comes_from_the_source_text(client):
    """This is extractive summarising: nothing may be invented."""
    body = (await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 3})).json()

    for bullet in body["bullets"]:
        assert bullet in SAMPLE


async def test_bullets_keep_their_original_order(client):
    body = (await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 3})).json()

    positions = [SAMPLE.index(bullet) for bullet in body["bullets"]]
    assert positions == sorted(positions)


async def test_asking_for_more_bullets_than_sentences_returns_them_all(client):
    short = "First sentence here. Second sentence here."
    body = (await client.post("/summarise", json={"text": short, "max_bullets": 10})).json()

    assert body["bullet_count"] == 2


async def test_max_bullets_defaults_when_omitted(client):
    body = (await client.post("/summarise", json={"text": SAMPLE})).json()
    assert body["bullet_count"] <= config.SUMMARY_BULLETS_DEFAULT


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


async def test_summarise_rejects_text_that_is_too_short(client):
    response = await client.post("/summarise", json={"text": "Too short.", "max_bullets": 2})
    assert response.status_code == 422


async def test_summarise_rejects_zero_bullets(client):
    response = await client.post("/summarise", json={"text": SAMPLE, "max_bullets": 0})
    assert response.status_code == 422


async def test_summarise_rejects_too_many_bullets(client):
    response = await client.post(
        "/summarise", json={"text": SAMPLE, "max_bullets": config.SUMMARY_BULLETS_MAX + 1}
    )
    assert response.status_code == 422


async def test_summarise_rejects_text_over_the_limit(client):
    huge = "word " * 3000  # comfortably past SUMMARY_TEXT_MAX
    response = await client.post("/summarise", json={"text": huge, "max_bullets": 3})
    assert response.status_code == 422


async def test_summarise_rejects_a_missing_text_field(client):
    response = await client.post("/summarise", json={"max_bullets": 3})
    assert response.status_code == 422


async def test_two_invalid_fields_are_both_reported(client):
    """The error list should name every problem, not just the first."""
    body = (await client.post("/summarise", json={"text": "short", "max_bullets": 50})).json()

    fields = {item["field"] for item in body["errors"]}
    assert "body.text" in fields
    assert "body.max_bullets" in fields
