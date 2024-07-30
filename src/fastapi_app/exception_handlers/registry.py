import types
import typing
from collections import abc

__all__ = ("register_exception", "get_exception_responses")


_VT = typing.TypeVar("_VT")
_KT = typing.TypeVar("_KT")


class InMemoryRegistry(abc.MutableMapping[_KT, _VT]):
    _registry: typing.Dict[_KT, _VT]

    def __init__(self):
        self._registry = dict()

    def __setitem__(self, __key: _KT, __value: _VT) -> None:
        if __key in self._registry:
            raise KeyError(f"{__key} already exists in registry")
        self._registry[__key] = __value

    def __delitem__(self, __key):
        raise TypeError(f"{self.__class__.__name__} has no delete method")

    def __getitem__(self, __key: _KT) -> _VT:
        return self._registry[__key]

    def __len__(self):
        return len(self._registry.keys())

    def __iter__(self):
        return iter(self._registry.keys())


Ex = typing.TypeVar("Ex", bound=typing.Type[Exception])
S = typing.TypeVar("S", bound=typing.Dict[int, typing.Dict])

__exception_registry = types.new_class("ExceptionRegistry", (InMemoryRegistry[Ex, S],), {})()


def register_exception(exc: Ex, status_code: int, response_model: typing.Any):
    __exception_registry[exc] = {
        status_code: {
            "model": response_model,
            "description": exc.__doc__,
        },
    }


def get_exception_responses(*exceptions: Ex) -> S:
    result = {}
    for exc in exceptions:
        result.update(__exception_registry[exc])
    return result
