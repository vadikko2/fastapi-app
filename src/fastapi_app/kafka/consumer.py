import asyncio
import logging
import typing

import aiokafka

__all__ = ("KafkaConsumer", "OnMessage")


logger = logging.getLogger(__name__)

OnMessage: typing.TypeAlias = typing.Callable[[aiokafka.ConsumerRecord], typing.Awaitable[None]]


class KafkaConsumer:
    def __init__(
        self,
        kafka_consumer: aiokafka.AIOKafkaConsumer,
        loop: asyncio.AbstractEventLoop,
    ):
        self._kafka_consumer = kafka_consumer
        self._loop = loop

    async def _consume(
        self,
        on_message: OnMessage,
        timeout_ms: float = 0,
        max_records: int | None = None,
    ):
        try:
            await self._kafka_consumer.start()
            logger.debug("AioKafka consumer has been started")
            while True:
                result = await self._kafka_consumer.getmany(
                    timeout_ms=timeout_ms,
                    max_records=max_records,
                )
                for tp, messages in result.items():
                    logger.debug(f"Got {len(messages)} messages from {tp.topic} topic")
                    if messages:
                        offset = messages[-1].offset + 1
                        for message in messages:
                            try:
                                await on_message(message)
                            except Exception as e:
                                logger.error(
                                    f"Failed to process message: {message.value}\ntopic: {message.topic}\n"
                                    f"partition: {message.partition}\nCause: {e}",
                                )
                                raise
                        logger.debug(f"Commit offset {offset}")
                        await self._kafka_consumer.commit({tp: offset})
        finally:
            await self._kafka_consumer.stop()

    def consume(self, on_message: OnMessage, timeout_ms: float = 0, max_records: int | None = None):
        """
        Прослушивает и обрабатывает события, приходящие из специфицированных топиков kafka.
        Больше про семантики чтения можно прочитать тут https://docs.confluent.io/kafka/design/delivery-semantics.html.
        В нашем случае необходимо использовать At Least One.
        Больше про Consume-минг можно прочитать тут https://aiokafka.readthedocs.io/en/stable/consumer.html.
        """
        self._loop.run_until_complete(self._consume(on_message, timeout_ms, max_records))
