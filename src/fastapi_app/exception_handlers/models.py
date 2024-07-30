import typing

import pydantic

__all__ = ("ErrorResponse", "ErrorResponseMulti")


class ErrorResponse(pydantic.BaseModel):
    """Error response model."""

    message: typing.Text = pydantic.Field(description="This field represent the message")
    path: typing.List = pydantic.Field(
        description="The path to the field that raised the error",
        default_factory=list,
    )


class ErrorResponseMulti(pydantic.BaseModel):
    """The public error response model that includes multiple objects."""

    results: pydantic.conlist(ErrorResponse, min_length=1)
