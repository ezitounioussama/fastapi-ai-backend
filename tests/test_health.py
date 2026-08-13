"""Tests for GET /health."""

from datetime import datetime, timezone

from app import config


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_returns_the_three_required_fields(client):
    """The brief asks for status, version and a timestamp."""
    body = (await client.get("/health")).json()

    assert set(body) == {"status", "version", "timestamp"}


async def test_health_status_is_ok(client):
    body = (await client.get("/health")).json()
    assert body["status"] == "ok"


async def test_health_version_matches_the_app_version(client):
    body = (await client.get("/health")).json()
    assert body["version"] == config.APP_VERSION


async def test_health_timestamp_is_parseable_and_recent(client):
    body = (await client.get("/health")).json()

    stamp = datetime.fromisoformat(body["timestamp"])

    # The value must carry a timezone; a naive datetime here would be ambiguous.
    assert stamp.tzinfo is not None

    # And it should be now, not a hard-coded or stale value.
    age = abs((datetime.now(timezone.utc) - stamp).total_seconds())
    assert age < 60


async def test_health_timestamp_changes_between_calls(client):
    """Proves the timestamp is generated per request, not fixed at import."""
    first = (await client.get("/health")).json()["timestamp"]
    second = (await client.get("/health")).json()["timestamp"]

    assert first != second


async def test_health_returns_json(client):
    response = await client.get("/health")
    assert response.headers["content-type"].startswith("application/json")


async def test_health_rejects_post(client):
    """/health is a GET endpoint; POST must not be allowed."""
    response = await client.post("/health")
    assert response.status_code == 405
