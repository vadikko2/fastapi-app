import dataclasses
import logging
import math
import time
import typing

import orjson
from fastapi import requests, responses
from starlette import types
from starlette.middleware.base import RequestResponseEndpoint

from fastapi_app.exception_handlers import exceptions
from fastapi_app.logging.models import RequestJsonLogSchema

__all__ = ("LoggingMiddleware",)

EMPTY_VALUE = ""
PORT = "8000"
PASS_ROUTES = [
    "/openapi.json",
    "/docs",
    "/health/database",
    "/health/redis",
]
ADMIN_ROUTE = "/admin"


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ReceiveProxy:
    """Proxy to starlette.types.Receive.__call__ with caching first receive call.
    https://github.com/tiangolo/fastapi/issues/394#issuecomment-994665859
    """

    receive: types.Receive
    cached_body: bytes
    _is_first_call: typing.ClassVar[bool] = True

    async def __call__(self):
        # First call will be for getting request body => returns cached result
        if self._is_first_call:
            self._is_first_call = False
            return {"type": "http.request", "body": self.cached_body, "more_body": False}

        return await self.receive()


class LoggingMiddleware:
    """Middleware that saves logs to JSON
    The main problem is
    After getting request_body
        body = await request.body()
    Body is removed from requests. I found solution as ReceiveProxy
    """

    @staticmethod
    async def get_protocol(request: requests.Request) -> str:
        protocol = str(request.scope.get("type", ""))
        http_version = str(request.scope.get("http_version", ""))
        if protocol.lower() == "http" and http_version:
            return f"{protocol.upper()}/{http_version}"
        return EMPTY_VALUE

    async def get_request_body(self, request: requests.Request) -> typing.Dict:
        body = await request.body()
        body = self.try_to_loads(body)
        request._receive = ReceiveProxy(receive=request.receive, cached_body=body)
        return body

    def try_to_loads(self, data) -> typing.Dict | typing.Any:
        try:
            return orjson.loads(data)
        except orjson.JSONDecodeError:
            return data

    async def __call__(self, request: requests.Request, call_next: RequestResponseEndpoint, *args, **kwargs):
        # logger.debug(f"Started Middleware: {__name__}")
        start_time = time.time()
        exception_object = None
        request_body = await self.get_request_body(request)
        server: typing.Tuple = request.get("server", ("localhost", PORT))
        request_headers: typing.Dict = dict(request.headers.items())

        # Response Side
        try:
            response = await call_next(request)
        except Exception as ex:
            logger.error(f"Exception: {ex}")
            response = exceptions.python_base_error_handler(request, ex)
            response_body = response.body
            exception_object = ex
            response_headers = {}
        else:
            response_headers = dict(response.headers.items())
            response_body = b""

            async for chunk in response.body_iterator:
                response_body += chunk

            response = responses.Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        # pass /openapi.json /docs /admin
        if request.url.path in PASS_ROUTES:
            return response
        if request.url.path.startswith(ADMIN_ROUTE):
            return response

        duration: int = math.ceil((time.time() - start_time) * 1000)

        # Initializing of json fields
        request_json_fields = RequestJsonLogSchema(
            # Request side
            request_uri=str(request.url),
            request_referer=request_headers.get("referer", EMPTY_VALUE),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            request_content_type=request_headers.get("content-type", EMPTY_VALUE),
            request_headers=request_headers,
            request_body=request_body if isinstance(request_body, dict) else EMPTY_VALUE,
            request_direction="in",
            request_x_api_key=request_headers.get("x-api-key"),
            # Response side
            response_status_code=response.status_code,
            response_size=int(response_headers.get("content-length", 0)),
            response_headers=response_headers,
            response_body=self.try_to_loads(response_body),
            duration=duration,
        ).model_dump(mode="json")

        message = (
            f'{"Error" if exception_object else "Answer"} '
            f"code: {response.status_code} "
            f'request url: {request.method} "{str(request.url)}" '
            f"duration: {duration} ms "
        )
        logger.info(
            message,
            extra={
                "request_json_fields": request_json_fields,
                "to_mask": True,
            },
            exc_info=exception_object,
        )
        return response
