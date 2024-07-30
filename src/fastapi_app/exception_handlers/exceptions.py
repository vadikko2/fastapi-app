"""
Используется для представления обработчиков ошибок FastAPI,
которые отправляются автоматически движком fastapi.
"""

import functools
import inspect
import typing

import decohints
from fastapi import encoders, exceptions, responses, status
from starlette import requests

from . import registry
from .models import ErrorResponse, ErrorResponseMulti

__all__ = (
    "bind_exception",
    "pydantic_request_validation_errors_handler",
    "python_base_error_handler",
)


Ex = typing.TypeVar("Ex", bound=Exception, contravariant=True)
ExceptionHandlerType: typing.TypeAlias = typing.Callable[[requests.Request, Ex], typing.Any]


@decohints.decohints
def bind_exception(status_code: int):
    """
    Привязка ответа ошибки к возвращаемому статус коду.

    Декорируемый обработчик должен содержать в себе аргументы: fastapi.Requests, Exception.
    Обязательно должен быть аннотируемым аргумент типа Exception, а также возвращаемый тип обработчика.

    ## Пример использования

    ```python
    from fastapi import Request, status

    @bind_exception(status_code=status.HTTP_404_NOT_FOUND)
    def not_found_handler(_: Request, error: ValueError) -> ErrorResponse:
        return ErrorResponse(message=error.message)
    ```

    Для получения описания ответа, объявленного обработчика, для OpenAPI схемы можно воспользоваться функцией
    `get_exception_responses`.

    ## Пример использования
    ```python
    from configurations.presentation.api.errors import registry

    exception_desc = registry.get_exception_responses(ValueError)

    router = fastapi.APIRouter(
        prefix="/some_router",
        tags=["Тестовый роутер"],
        responses=exception_desc,
    )
    ```
    """

    def decorator(func: ExceptionHandlerType):
        @functools.wraps(func)
        def wrapper(request: requests.Request, error: Ex) -> responses.JSONResponse:
            response = func(request, error)
            return responses.JSONResponse(
                content=encoders.jsonable_encoder(response),
                status_code=status_code,
            )

        spec = inspect.signature(func)
        response_model = spec.return_annotation
        if response_model is None:
            raise AttributeError("There is no annotation of the returned type")
        spec = inspect.getfullargspec(func)
        exc = spec.annotations.get(spec.args[1])
        if not issubclass(exc, Exception):
            raise AttributeError('There is no annotation of the "error" arg type')
        registry.register_exception(exc, status_code, response_model)

        return wrapper

    return decorator


@bind_exception(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
def python_base_error_handler(_: requests.Request, error: Exception) -> ErrorResponseMulti:
    return ErrorResponseMulti(results=[ErrorResponse(message=f"Unhandled error: {error}")])


@bind_exception(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
def pydantic_request_validation_errors_handler(
    _: requests.Request,
    error: exceptions.RequestValidationError,
) -> ErrorResponseMulti:
    """This function is called if the Pydantic validation error was raised."""

    return ErrorResponseMulti(
        results=[
            ErrorResponse(
                message=err["msg"],
                path=list(err["loc"]),
            )
            for err in error.errors()
        ],
    )
