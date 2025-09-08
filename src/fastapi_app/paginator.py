import math
import typing

import pydantic

T = typing.TypeVar("T")


class PaginatedResult(pydantic.BaseModel, typing.Generic[T]):
    current_page: pydantic.PositiveInt = pydantic.Field(
        description="Номер текущей страницы",
    )
    total: pydantic.NonNegativeInt = pydantic.Field(
        description="Общее количество элементов",
    )
    data: typing.List[T] = pydantic.Field(
        frozen=True,
        description="Список объектов результата страницы",
    )
    limit: pydantic.PositiveInt = pydantic.Field(
        exclude=True,
        description="Ограничение количества выдачи на страницу",
    )
    url: pydantic.HttpUrl | None = pydantic.Field(
        default=None,
        exclude=True,
        description="URL путь роута для формировании ссылок на страницы пагинации",
    )

    @pydantic.computed_field(description="Количество объектов результата страницы")
    def count(self) -> pydantic.NonNegativeInt:
        return len(self.data)

    @pydantic.model_validator(mode="after")
    def _validate_total(self) -> typing.Self:
        self.total = self.total if self.total >= self.count else self.count
        self.limit = self.limit if self.limit >= self.count else self.total
        self.current_page = max(1, min(self.current_page, self.total_pages))
        return self

    @pydantic.computed_field(description="Всего страниц")
    @property
    def total_pages(self) -> pydantic.PositiveInt:
        return math.ceil(self.total / self.limit)

    @pydantic.computed_field(description="Номер следующей страницы")
    def next_page(self) -> pydantic.NonNegativeInt | None:
        return None if self.current_page >= self.total_pages else self.current_page + 1

    @pydantic.computed_field(description="Номер предыдущей страницы")
    def previous_page(self) -> pydantic.NonNegativeInt | None:
        return None if self.current_page <= 1 else self.current_page - 1

    def _get_url_page(self, page: pydantic.PositiveInt) -> typing.Text | None:
        if not self.url:
            return None
        query_params = {k: v for k, v in self.url.query_params()}
        query_params.update({"page": page, "limit": self.limit})
        return str(
            pydantic.HttpUrl.build(
                scheme=self.url.scheme,
                username=self.url.username,
                password=self.url.password,
                host=self.url.host,
                port=self.url.port,
                path=self.url.path and self.url.path.removeprefix("/"),
                query="&".join(f"{k}={v}" for k, v in query_params.items()),
                fragment=self.url.fragment,
            ),
        )

    @pydantic.computed_field(description="Ссылка на следующую страницу пагинации")
    def next_page_url(self) -> typing.Text | None:
        return self.next_page and self._get_url_page(self.next_page)

    @pydantic.computed_field(description="Ссылка на предыдущую страницу пагинации")
    def previous_page_url(self) -> typing.Text | None:
        return self.previous_page and self._get_url_page(self.previous_page)

    @pydantic.computed_field(description="Ссылка на первую страницу пагинации")
    def first_page_url(self) -> typing.Text | None:
        return self._get_url_page(1)

    @pydantic.computed_field(description="Ссылка на последнюю страницу пагинации")
    def last_page_url(self) -> typing.Text | None:
        return self._get_url_page(self.total_pages)
