import typing

import pydantic

__all__ = ("Response",)

R = typing.TypeVar("R", bound=pydantic.BaseModel)


class Response(pydantic.BaseModel, typing.Generic[R]):
    """Generic response model that consist only one result."""

    error_code: int | None = None
    error_message: typing.Text | None = None
    result: R | None = None
