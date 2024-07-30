import asyncio

import fastapi
import httpx
import pytest
from fastapi import responses, status
from opentelemetry.sdk import trace
from opentelemetry.sdk.trace import export
from opentelemetry.sdk.trace.export import in_memory_span_exporter

import fastapi_app
from tests.mock import idempotency_mock_api


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    try:
        yield loop
    finally:
        if loop.is_running():
            loop.close()


def get_test_client(app: fastapi.FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(app=app, base_url="http://test-api")


@pytest.fixture
def api_with_telemetry() -> httpx.AsyncClient:
    app = fastapi_app.create(
        title="Test",
        debug=True,
        description="Telemetry test API",
        telemetry_enable=True,
    )

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    return get_test_client(app)


@pytest.fixture
def span_exporter() -> in_memory_span_exporter.InMemorySpanExporter:
    tracer_provider: trace.TracerProvider = trace.trace_api.get_tracer_provider()
    span_exporter = in_memory_span_exporter.InMemorySpanExporter()
    span_processor = export.SimpleSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    return span_exporter


@pytest.fixture
def api_with_auth() -> httpx.AsyncClient:
    app = fastapi_app.create(
        title="Test",
        debug=True,
        description="Auth test API",
        auth_require=True,
        auth_key_pattern="API_KEY_",
        ignore_auth_methods=["/ignoring_auth"],
    )

    @app.post("/ignoring_auth", status_code=status.HTTP_200_OK)
    async def ignoring_auth_route():
        return responses.JSONResponse({}, status_code=status.HTTP_200_OK)

    @app.post("/auth", status_code=status.HTTP_200_OK)
    async def auth_route():
        return responses.JSONResponse({}, status_code=status.HTTP_200_OK)

    return get_test_client(app)


@pytest.fixture
def api_with_idempotency() -> httpx.AsyncClient:
    return get_test_client(idempotency_mock_api.mock_app)
