import os
import typing

from fastapi.security import APIKeyHeader
from starlette import exceptions, requests, status


class ValidateAPIKeyHeader(APIKeyHeader):
    def __init__(
        self,
        header_name: typing.Text,
        api_keys: typing.Set[typing.Text],
    ) -> None:
        self._api_keys = api_keys
        super().__init__(name=header_name, auto_error=False)

    async def __call__(self, request: requests.Request) -> typing.Text:
        api_key = await super().__call__(request)

        if api_key is None or api_key not in self._api_keys:
            raise exceptions.HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        return api_key


def get_api_keys_from_env(api_auth_key_prefix: typing.Text) -> typing.Set[typing.Text]:
    return {
        value
        for key, value in os.environ.items()
        if key.startswith(api_auth_key_prefix)
    }
