import functools
import typing

_T = typing.TypeVar("_T")
_P = typing.ParamSpec("_P")


def _call_once(func: typing.Callable[_P, _T | None]) -> typing.Callable[_P, _T | None]:
    _called = False

    @functools.wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T | None:
        nonlocal _called
        if not _called:
            try:
                return func(*args, **kwargs)
            finally:
                _called = True

    return wrapper


@_call_once
def configure_sentry(dsn: typing.Text) -> None:
    import sentry_sdk

    sentry_sdk.init(dsn)
