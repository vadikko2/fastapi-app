import asyncio
import typing

from opentelemetry.instrumentation import httpx as ot_httpx
from opentelemetry.instrumentation import logging as ot_logging
from opentelemetry.instrumentation import redis as ot_redis
from opentelemetry.instrumentation import sqlalchemy as ot_sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine

from fastapi_app.kafka import consumer, dependencies
from fastapi_app.telemetry import telemetry


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
) -> consumer.KafkaConsumer:
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    if telemetry_enable:
        telemetry.init_tracer(
            service_name=f"{app_title}_{env_title}",
            timeout=telemetry_traces_timeout,
            endpoint=telemetry_traces_endpoint,
        )
        ot_httpx.HTTPXClientInstrumentor().instrument()
        ot_redis.RedisInstrumentor().instrument()
        if telemetry_db_engine:
            ot_sqlalchemy.SQLAlchemyInstrumentor().instrument(engine=telemetry_db_engine.sync_engine)
        ot_logging.LoggingInstrumentor().instrument()
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
        ),
        loop=loop,
    )
