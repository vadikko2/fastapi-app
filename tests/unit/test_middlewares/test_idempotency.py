import uuid

from fastapi import status

from tests.mock import idempotency_mock_api


class TestIdempotencyMiddleware:
    async def test_idempotency_positive(self, api_with_idempotency):
        body = idempotency_mock_api.Foo(bar=uuid.uuid4())
        idempotency_id = uuid.uuid4()
        await api_with_idempotency.post(
            "/idempotency",
            headers={"Idempotency-Key": str(idempotency_id)},
            json=body.model_dump(mode="json"),
        )

        response = await api_with_idempotency.post(
            "/idempotency",
            headers={"Idempotency-Key": str(idempotency_id)},
            json=body.model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_idempotency_negative(self, api_with_idempotency):
        body = idempotency_mock_api.Foo(bar=uuid.uuid4())
        await api_with_idempotency.post(
            "/idempotency",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json=body.model_dump(mode="json"),
        )

        response = await api_with_idempotency.post(
            "/idempotency",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json=body.model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_409_CONFLICT
