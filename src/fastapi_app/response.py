import typing

import pydantic

__all__ = (
    "ResponseMulti",
    "Response",
)

R = typing.TypeVar("R", bound=pydantic.BaseModel)


class ResponseMulti(pydantic.BaseModel, typing.Generic[R]):
    """Generic response model that consist multiple results."""

    result: typing.List[R]


class Response(pydantic.BaseModel, typing.Generic[R]):
    """Generic response model that consist only one result."""

    result: R
