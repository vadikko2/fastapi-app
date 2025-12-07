import typing

import pydantic


class BaseJsonLogSchema(pydantic.BaseModel):
    """
    Main log in JSON format
    """

    timestamp: typing.Text = pydantic.Field(alias="@timestamp")
    thread: typing.Union[pydantic.NonNegativeInt, typing.Text] | None = pydantic.Field(
        alias="process.pid",
        default=None,
    )
    message: typing.Text
    level_name: typing.Text = pydantic.Field(alias="log.level")
    app_name: typing.Text = pydantic.Field(alias="service.origin.name")
    app_version: typing.Text = pydantic.Field(alias="service.origin.version")
    app_env: typing.Text | None = pydantic.Field(
        alias="service.origin.environment",
        default=None,
    )
    log_origin_function: typing.Text | None = pydantic.Field(
        alias="log.origin.function",
        default=None,
    )
    log_origin_file_line: pydantic.NonNegativeInt | None = pydantic.Field(
        alias="log.origin.file.line",
        default=None,
    )
    log_origin_file_name: typing.Text | None = pydantic.Field(
        alias="log.origin.file.name",
        default=None,
    )
    log_file_path: typing.Text | None = pydantic.Field(
        alias="log.file.path",
        default=None,
    )
    trace_id: typing.Text | None = pydantic.Field(alias="trace.id", default=None)
    span_id: typing.Text | None = pydantic.Field(alias="span.id", default=None)
    parent_id: typing.Text | None = pydantic.Field(alias="parent.id", default=None)
    transaction_id: typing.Text | None = pydantic.Field(
        alias="transaction.id",
        default=None,
    )
    duration: pydantic.NonNegativeInt | None = None
    labels: typing.Dict | None = None
    tags: typing.List[typing.Text] | None = None

    model_config = pydantic.ConfigDict(populate_by_name=True)


class RequestJsonLogSchema(pydantic.BaseModel):
    """
    Schema for request/response answer
    """

    url_path: typing.Text = pydantic.Field(alias="url.path")
    url_query: typing.Text = pydantic.Field(alias="url.query")
    http_request_method: typing.Text = pydantic.Field(alias="http.request.method")
    http_request_mime_type: typing.Text = pydantic.Field(alias="http.request.mime_type")
    http_request_idempotency_key: typing.Text = pydantic.Field(
        alias="http.request.idempotency_key",
    )
    http_request_body_content: typing.Union[typing.Dict, bytes, str] = pydantic.Field(
        alias="http.request.body.content",
    )
    http_request_body_bytes: pydantic.NonNegativeInt = pydantic.Field(
        alias="http.request.body.bytes",
        default=int(0),
    )
    http_request_referer: typing.Text = pydantic.Field(alias="http.request.referer")
    http_response_status_code: pydantic.PositiveInt = pydantic.Field(
        alias="http.response.status_code",
    )
    http_response_body_content: typing.Union[typing.Dict, bytes, typing.List] = (
        pydantic.Field(
            alias="http.response.body.content",
        )
    )
    http_response_body_bytes: pydantic.NonNegativeInt = pydantic.Field(
        alias="http.response.body.bytes",
        default=int(0),
    )
    http_response_mime_type: typing.Text | None = pydantic.Field(
        alias="http.response.mime_type",
        default=None,
    )
    user_id: typing.Text | None = pydantic.Field(alias="user.id", default=None)
    user_domain: typing.Text | None = pydantic.Field(alias="user.domain", default=None)
    operation: typing.Text | None = None

    model_config = pydantic.ConfigDict(populate_by_name=True)
