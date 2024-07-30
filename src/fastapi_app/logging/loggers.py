import logging
import types
import typing

import loguru


class ConsoleLogger(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Get corresponding Loguru level if it exists
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 1
        frame = typing.cast(types.FrameType, frame.f_back)
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = typing.cast(types.FrameType, frame.f_back)
            depth += 1
        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )
