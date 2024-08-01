import inspect
import itertools
import typing

import dotenv
import fastapi
import fastapi_key_auth
import sqladmin
from fastapi import exceptions as fastapi_exceptions
from fastapi.middleware import cors
from idempotency_header_middleware import middleware as idempotency_middleware
from idempotency_header_middleware.backends import base
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette import types

from fastapi_app.exception_handlers import exceptions, registry
from fastapi_app.logging import middleware as logging_middleware

__all__ = ("create",)
dotenv.load_dotenv()

Ex = typing.TypeVar("Ex", bound=Exception, contravariant=True)
ExceptionHandlerType: typing.TypeAlias = typing.Callable[[fastapi.Request, Ex], typing.Any]


def create(
    *_,
    env_title: str | None = None,
    command_routers: typing.Iterable[fastapi.APIRouter] | None = None,
    query_routers: typing.Iterable[fastapi.APIRouter] | None = None,
    healthcheck_routers: typing.Iterable[fastapi.APIRouter] | None = None,
    lifespan_handler: types.Lifespan[types.AppType] | None = None,
    global_dependencies: typing.Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]] | None = None,
    command_dependencies: typing.Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]] | None = None,
    query_dependencies: typing.Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]] | None = None,
    admin_factory: typing.Callable[[fastapi.FastAPI], sqladmin.Admin] | None = None,
    admin_views: typing.Iterable[typing.Type[sqladmin.ModelView]] | None = None,
    idempotency_require: bool = False,
    idempotency_backed: base.Backend | None = None,
    idempotency_enforce_uuid4: bool = True,
    idempotency_methods: typing.List[typing.Text] | None = None,
    auth_require: bool = False,
    auth_key_pattern: typing.Text = "API_KEY_",
    ignore_auth_methods: typing.List[typing.Text] = None,
    telemetry_enable: bool = False,
    telemetry_traces_endpoint: str = "http://localhost:4318/v1/traces",
    telemetry_traces_timeout: int = 10,
    telemetry_db_engine: AsyncEngine | None = None,
    exception_handlers: typing.Iterable[ExceptionHandlerType] | None = None,
    cors_enable: bool = False,
    cors_allow_origins: typing.List[typing.Text] | None = None,
    cors_allow_methods: typing.List[typing.Text] | None = None,
    cors_allow_headers: typing.List[typing.Text] | None = None,
    cors_allow_credentials: bool = True,
    **kwargs,
) -> fastapi.FastAPI:
    global_dependencies = global_dependencies or []
    command_dependencies = command_dependencies or []
    query_dependencies = query_dependencies or []
    healthcheck_routers = healthcheck_routers or []

    # Инициализирует приложение FastAPI
    app = fastapi.FastAPI(
        **kwargs,
        dependencies=global_dependencies,
        lifespan=lifespan_handler,
        responses=registry.get_exception_responses(Exception, fastapi_exceptions.RequestValidationError),
    )

    # Include REST API routes
    for router in command_routers or []:
        app.include_router(router, dependencies=command_dependencies)
    for router in query_routers or []:
        app.include_router(router, dependencies=query_dependencies)
    for router in healthcheck_routers or []:
        app.include_router(router)

    # Расширяет default обработчики ошибок FastAPI
    if exception_handlers:
        default_handlers = [exceptions.python_base_error_handler, exceptions.pydantic_request_validation_errors_handler]
        for handler in itertools.chain(exception_handlers, default_handlers):
            spec = inspect.getfullargspec(handler)
            error_type = spec.annotations.get(spec.args[1])
            app.exception_handler(error_type)(handler)

    # Настраиваем Middleware
    if idempotency_require:
        app.add_middleware(
            idempotency_middleware.IdempotencyHeaderMiddleware,
            backend=idempotency_backed,
            applicable_methods=idempotency_methods or [],
            enforce_uuid4_formatting=idempotency_enforce_uuid4,
        )
    if auth_require:
        app.add_middleware(
            fastapi_key_auth.AuthorizerMiddleware,
            public_paths=ignore_auth_methods or [],
            key_pattern=auth_key_pattern,
        )

    app.middleware("http")(logging_middleware.LoggingMiddleware())
    if cors_enable:
        app.add_middleware(
            cors.CORSMiddleware,
            allow_origins=cors_allow_origins or ["*"],
            allow_credentials=cors_allow_credentials,
            allow_methods=cors_allow_methods or ["*"],
            allow_headers=cors_allow_headers or ["*"],
        )

    if admin_factory:
        admin_app = admin_factory(app)
        for view in admin_views:
            admin_app.add_view(view)

    if telemetry_enable:
        from opentelemetry.instrumentation import fastapi as ot_fastapi
        from opentelemetry.instrumentation import logging as ot_logging
        from opentelemetry.instrumentation import redis as ot_redis
        from opentelemetry.instrumentation import sqlalchemy as ot_sqlalchemy

        from fastapi_app.telemetry import telemetry

        title = f"{app.title}_{env_title}" if env_title else app.title
        telemetry.init_tracer(service_name=title, timeout=telemetry_traces_timeout, endpoint=telemetry_traces_endpoint)
        ot_fastapi.FastAPIInstrumentor.instrument_app(app)
        ot_redis.RedisInstrumentor().instrument()
        if telemetry_db_engine:
            ot_sqlalchemy.SQLAlchemyInstrumentor().instrument(engine=telemetry_db_engine.sync_engine)
        ot_logging.LoggingInstrumentor().instrument()

    return app
