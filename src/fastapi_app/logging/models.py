import typing

import pydantic


class BaseJsonLogSchema(pydantic.BaseModel):
    """
    Main log in JSON format
    """

    thread: typing.Union[int, str]
    level_name: str
    message: str
    source_log: str
    timestamp: str
    app_name: str
    app_version: str
    # app_env: str
    duration: int
    exceptions: typing.Union[typing.List[str], str] = None
    trace_id: str = None
    span_id: str = None
    parent_id: str = None

    model_config = pydantic.ConfigDict(populate_by_name=True)


class RequestJsonLogSchema(pydantic.BaseModel):
    """
    Schema for request/response answer
    """

    request_uri: str
    request_referer: str
    request_method: str
    request_path: str
    request_host: str
    request_size: int
    request_content_type: str
    request_headers: dict
    request_body: dict | bytes
    request_direction: str
    request_x_api_key: str | None = None
    response_status_code: int
    response_size: int
    response_headers: dict
    response_body: dict | str
    duration: int
