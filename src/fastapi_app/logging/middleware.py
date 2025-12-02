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
            return {
                "type": "http.request",
                "body": self.cached_body,
                "more_body": False,
            }

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
        request._receive = ReceiveProxy(  # pyright: ignore[reportArgumentType]
            receive=request.receive,
            cached_body=body,
        )
        return body

    def try_to_loads(self, data) -> typing.Dict | typing.Any:
        try:
            return orjson.loads(data)
        except orjson.JSONDecodeError:
            return data

    @staticmethod
    def _is_binary_content_type(content_type: str) -> bool:
        """Check if content type is binary (image, video, audio, etc.)"""
        if not content_type:
            return False

        binary_types = [
            "image/",
            "video/",
            "audio/",
            "application/octet-stream",
            "application/pdf",
            "application/zip",
            "application/x-tar",
            "application/gzip",
        ]

        return any(content_type.startswith(binary_type) for binary_type in binary_types)

    async def __call__(
        self,
        request: requests.Request,
        call_next: RequestResponseEndpoint,
        *args,
        **kwargs,
    ):
        # logger.debug(f"Started Middleware: {__name__}")
        start_time = time.time()
        exception_object = None
        request_body = await self.get_request_body(request)
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
            original_media_type = response.headers.get("content-type", "")

            async for chunk in response.body_iterator:
                response_body += chunk

            # Preserve original media type, don't force application/json
            media_type = (
                original_media_type.split(";")[0] if original_media_type else None
            )
            if not media_type:
                # Try to get from response if available
                if hasattr(response, "media_type") and response.media_type:
                    media_type = response.media_type
                else:
                    media_type = "application/json"

            response = responses.Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=media_type,
            )

        # pass /openapi.json /docs /admin
        if request.url.path in PASS_ROUTES:
            return response
        if request.url.path.startswith(ADMIN_ROUTE):
            return response

        duration: int = math.ceil((time.time() - start_time) * 1000)

        # Check if response is binary (image, video, etc.)
        response_media_type = (
            response.headers.get("content-type", "").split(";")[0].lower()
        )
        is_binary_response = self._is_binary_content_type(response_media_type)

        # For binary responses, don't try to parse as JSON
        if is_binary_response:
            response_body_content = f"<binary data: {response_media_type}>"
        else:
            response_body_content = self.try_to_loads(response_body)

        # Initializing of json fields
        request_json_fields = RequestJsonLogSchema(
            # Request side
            url_path=str(request.url.path),
            url_query=str(request.url.query),
            http_request_referer=request_headers.get("referer", EMPTY_VALUE),
            http_request_method=request.method,
            http_request_mime_type=request_headers.get("content-type", EMPTY_VALUE),
            http_request_idempotency_key=request_headers.get(
                "idempotency-key",
                EMPTY_VALUE,
            ),
            http_request_body_content=request_body,
            http_request_body_bytes=int(request_headers.get("content-length", 0)),
            # Response side
            http_response_status_code=response.status_code,
            http_response_body_bytes=int(response_headers.get("content-length", 0)),
            http_response_body_content=response_body_content,
            duration=duration,
        ).model_dump(mode="json", by_alias=True)

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
