import datetime
import json
import logging
import sys
import traceback
import typing

from fastapi_app.logging import loggers
from fastapi_app.logging.models import BaseJsonLogSchema

__all__ = ("generate_log_config",)


class JSONLogFormatter(logging.Formatter):
    """
    Custom class-formatter for writing logs to json
    """

    def __init__(self, app_name: str | None = None, app_version: str | None = None):
        super().__init__()

        self.app_name = app_name
        self.app_version = app_version

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        """
        Formatting LogRecord to json

        :param record: logging.LogRecord
        :return: json string
        """
        log_object: dict = self._format_log_object(record)
        return json.dumps(log_object, ensure_ascii=False)

    def _format_log_object(self, record: logging.LogRecord) -> dict:
        now = datetime.datetime.fromtimestamp(record.created).astimezone().replace(microsecond=0).isoformat()
        message = record.getMessage()
        duration = record.duration if hasattr(record, "duration") else record.msecs
        span_id = record.otelSpanID if hasattr(record, "otelSpanID") else None
        trace_id = record.otelTraceID if hasattr(record, "otelTraceID") else None

        json_log_fields = BaseJsonLogSchema(
            thread=record.process,
            timestamp=now,
            level_name=logging.getLevelName(record.levelno),
            message=message,
            source_log=record.name,
            duration=duration,
            app_name=self.app_name,
            app_version=self.app_version,
        )

        if hasattr(record, "props"):
            json_log_fields.props = record.props

        if record.exc_info:
            json_log_fields.exceptions = traceback.format_exception(*record.exc_info)

        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        if span_id and trace_id:
            json_log_fields.span_id = span_id
            json_log_fields.trace_id = trace_id

        # Pydantic to dict
        json_log_object = json_log_fields.model_dump(
            exclude_unset=True,
            by_alias=True,
        )

        # getting additional fields
        if hasattr(record, "request_json_fields"):
            json_log_object.update(record.request_json_fields)

        return json_log_object


def generate_log_config(
    logging_level: str,
    serialize: bool = False,
    app_name: str | None = None,
    app_version: str | None = None,
) -> dict[str, typing.Any]:
    handler = ["json"] if serialize else ["intercept"]

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONLogFormatter,
                "app_name": app_name,
                "app_version": app_version,
            },
        },
        "handlers": {
            "json": {
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
            },
            "intercept": {
                "()": loggers.ConsoleLogger,
            },
        },
        "loggers": {
            "root": {
                "handlers": handler,
                "level": logging_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": handler,
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": handler,
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
