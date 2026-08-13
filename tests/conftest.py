"""Shared test fixtures.

The client is httpx's AsyncClient wired straight to the app through
ASGITransport. That sends requests in-process — no server to start, no port to
pick, and no network involved — while still going through the real routing,
validation and serialisation stack.

This is used instead of fastapi.testclient.TestClient because Starlette now
warns that TestClient with httpx is deprecated in favour of httpx2. Calling
httpx directly avoids the deprecation and matches the brief's "pytest and
httpx" requirement literally.
"""

import httpx
import pytest_asyncio

from app.main import app

BASE_URL = "http://testserver"


@pytest_asyncio.fixture
async def client():
    """An httpx client that talks to the FastAPI app in-process."""
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as async_client:
        yield async_client
