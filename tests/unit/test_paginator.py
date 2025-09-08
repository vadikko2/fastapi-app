import math

import pytest

from fastapi_app import paginator as fastapi_paginator


class TestPaginator:
    def test_paginate_positive(self):
        # Проверка на генерацию корректной пагинации
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        page = 2
        total = 100
        limit = len(data)
        url = f"http://test_url.ru/path?query=1&limit={limit}"

        result = fastapi_paginator.PaginatedResult[int](
            data=data,
            current_page=page,
            total=total,
            limit=limit,
            url=url,
        )

        assert result.count == len(data)
        assert result.current_page == page
        assert result.total_pages == math.ceil(total / limit)
        assert result.next_page == result.current_page + 1
        assert result.previous_page == result.current_page - 1
        assert result.next_page_url == str(url + f"&page={result.next_page}")
        assert result.previous_page_url == str(url + f"&page={result.previous_page}")

    def test_paginate_with_less_total_then_result_positive(self):
        # Проверка на генерацию корректной пагинации в случае, если у нас total или limit меньше чем количество в data
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        page = 2
        total = 5
        limit = 5
        url = "http://test_url.ru/path?query=1&limit={}"

        result = fastapi_paginator.PaginatedResult[int](
            data=data,
            current_page=page,
            total=total,
            limit=limit,
            url=url.format(limit),
        )

        assert result.count == len(data)
        assert result.total_pages == 1
        assert result.total == len(data)
        assert result.limit == len(data)
        assert result.current_page == 1
        assert result.next_page is None
        assert result.previous_page is None
        assert result.next_page_url is None
        assert result.previous_page_url is None
        assert (
            result.last_page_url
            == result.first_page_url
            == url.format(len(data)) + "&page=1"
        )

    @pytest.mark.parametrize("page", [10, 9999])
    def test_paginate_with_last_page_positive(self, page):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        total = 100
        limit = len(data)
        url = f"http://test_url.ru/path?query=1&limit={limit}"

        result = fastapi_paginator.PaginatedResult[int](
            data=data,
            current_page=page,
            total=total,
            limit=limit,
            url=url,
        )

        assert result.current_page == math.ceil(total / limit)
        assert result.next_page is None
        assert result.previous_page == result.current_page - 1
        assert result.next_page_url is None
        assert result.previous_page_url == url + f"&page={result.previous_page}"
        assert result.last_page_url == url + f"&page={result.total_pages}"
        assert result.first_page_url == url + "&page=1"

    def test_paginate_with_first_page_positive(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        total = 100
        limit = len(data)
        url = f"http://test_url.ru/path?query=1&limit={limit}"
        page = 1

        result = fastapi_paginator.PaginatedResult[int](
            data=data,
            current_page=page,
            total=total,
            limit=limit,
            url=str(url),
        )

        assert result.current_page == 1
        assert result.next_page == result.current_page + 1
        assert result.previous_page is None
        assert result.next_page_url == url + f"&page={result.next_page}"
        assert result.previous_page_url is None
        assert result.first_page_url == url + "&page=1"
        assert result.last_page_url == url + f"&page={result.total_pages}"
