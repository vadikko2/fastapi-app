import asyncio
import logging
import ssl
import typing

from sqlalchemy.ext.asyncio import AsyncEngine

from fastapi_app.kafka import consumer, dependencies
from fastapi_app.telemetry import sentry

logger = logging.getLogger(__name__)


def create(
    app_title: typing.Text,
    env_title: typing.Text,
    dsn: typing.Text,
    security_protocol: typing.Text,
    sasl_mechanism: typing.Text,
    user: typing.Text,
    password: typing.Text,
    max_wait_ms: int,
    group_id: typing.Text,
    topics: typing.Iterable[typing.Text],
    telemetry_enable: bool = False,
    telemetry_traces_endpoint: str = "http://localhost:4318/v1/traces",
    telemetry_traces_timeout: int = 10,
    telemetry_db_engine: AsyncEngine | None = None,
    sentry_enable: bool = False,
    sentry_dsn: str | None = None,
    ssl_context: ssl.SSLContext | None = None,
) -> consumer.KafkaConsumer:
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    if telemetry_enable:
        from opentelemetry.instrumentation import aiokafka as ot_aiokafka
        from opentelemetry.instrumentation import httpx as ot_httpx
        from opentelemetry.instrumentation import logging as ot_logging
        from opentelemetry.instrumentation import redis as ot_redis
        from opentelemetry.instrumentation import sqlalchemy as ot_sqlalchemy

        from fastapi_app.telemetry import telemetry

        telemetry.init_tracer(
            service_name=f"{app_title}_{env_title}",
            timeout=telemetry_traces_timeout,
            endpoint=telemetry_traces_endpoint,
        )
        ot_httpx.HTTPXClientInstrumentor().instrument()
        ot_redis.RedisInstrumentor().instrument()
        if telemetry_db_engine:
            ot_sqlalchemy.SQLAlchemyInstrumentor().instrument(
                engine=telemetry_db_engine.sync_engine,
            )
        ot_logging.LoggingInstrumentor().instrument()
        ot_aiokafka.AIOKafkaInstrumentor().instrument()
    if sentry_enable and sentry_dsn:
        logger.warning(
            "Sentry configuration with bootstrap is deprecated."
            "Call `telemetry.sentry:configure_sentry` directly "
            "at the start of your application to handle all errors "
            "including ones happening during initialization.",
        )
        sentry.configure_sentry(sentry_dsn)

    return consumer.KafkaConsumer(
        dependencies.kafka_consumer_factory(
            topics=topics,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=user,
            sasl_plain_password=password,
            bootstrap_servers=dsn,
            fetch_max_wait_ms=max_wait_ms,
            group_id=group_id,
            loop=loop,
            ssl_context=ssl_context,
        ),
        loop=loop,
    )
