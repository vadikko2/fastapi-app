import os

from fastapi import status

os.environ["API_KEY_TEST"] = "some_test_auth_key"


class TestAuthMiddleware:
    async def test_auth_positive(self, api_with_auth):
        response = await api_with_auth.post("/auth", headers={"x-api-key": str(os.environ["API_KEY_TEST"])})
        assert response.status_code == status.HTTP_200_OK

    async def test_auth_negative(self, api_with_auth):
        response = await api_with_auth.post("/auth")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_auth_with_invalid_key_negative(self, api_with_auth):
        response = await api_with_auth.post("/auth", headers={"x-api-key": "invalid_some_key"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_ignoring_auth_route_positive(self, api_with_auth):
        response = await api_with_auth.post(url="/ignoring_auth")
        assert response.status_code == status.HTTP_200_OK
