import asyncio
import ssl
import typing

import aiokafka

__all__ = ("kafka_consumer_factory",)


def kafka_consumer_factory(
    topics: typing.Iterable[typing.Text],
    security_protocol: typing.Text,
    sasl_mechanism: typing.Text,
    sasl_plain_username: typing.Text,
    sasl_plain_password: typing.Text,
    bootstrap_servers: typing.Text,
    fetch_max_wait_ms: int,
    group_id: typing.Text,
    loop: asyncio.AbstractEventLoop,
    ssl_context: ssl.SSLContext | None = None,
) -> aiokafka.AIOKafkaConsumer:
    return aiokafka.AIOKafkaConsumer(
        *topics,
        security_protocol=security_protocol,
        sasl_mechanism=sasl_mechanism,
        sasl_plain_username=sasl_plain_username,
        sasl_plain_password=sasl_plain_password,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        fetch_max_wait_ms=fetch_max_wait_ms,
        group_id=group_id,
        enable_auto_commit=False,
        loop=loop,
        ssl_context=ssl_context,
    )
