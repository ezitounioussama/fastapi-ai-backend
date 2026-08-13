"""Tests for the index route and the generated documentation."""


async def test_root_lists_the_endpoints(client):
    body = (await client.get("/")).json()

    assert body["version"]
    for path in ("/health", "/chat", "/quiz", "/summarise"):
        assert path in body["endpoints"]


async def test_openapi_schema_is_served(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]
    for path in ("/health", "/chat", "/quiz", "/summarise"):
        assert path in paths, f"{path} missing from the OpenAPI schema"


async def test_swagger_ui_loads(client):
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


async def test_limits_appear_in_the_schema(client):
    """The Pydantic limits must reach the docs, or they are undiscoverable."""
    schema = (await client.get("/openapi.json")).json()
    quiz_schema = schema["components"]["schemas"]["QuizRequest"]["properties"]

    assert quiz_schema["num_questions"]["minimum"] == 1
    assert quiz_schema["num_questions"]["maximum"] == 10


async def test_unknown_route_returns_404(client):
    response = await client.get("/nope")
    assert response.status_code == 404
