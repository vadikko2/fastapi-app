import uuid

import pydantic
from fastapi import responses, status
from idempotency_header_middleware import backends

import fastapi_app

mock_storage = set()
mock_app = fastapi_app.create(
    debug=True,
    description="Mock API",
    middlewares=[],
    startup_tasks=[],
    shutdown_tasks=[],
    global_dependencies=[],
    idempotency_require=True,
    idempotency_backed=backends.MemoryBackend(),
    idempotency_methods=["POST", "DELETE", "PUT"],
    auth_require=False,
)


class Foo(pydantic.BaseModel):
    bar: uuid.UUID


@mock_app.post("/idempotency", status_code=status.HTTP_200_OK)
async def mock_create_something(body: Foo):
    if body.bar in mock_storage:
        return responses.JSONResponse({}, status_code=status.HTTP_409_CONFLICT)
    else:
        mock_storage.add(body.bar)
        return responses.JSONResponse({}, status_code=status.HTTP_200_OK)
