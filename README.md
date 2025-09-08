- [fastapi-app-generator](#fastapi-app-generator)
  - [Установка](#установка)
  - [Быстрый старт](#быстрый-старт)
    - [Список параметров `fastapi_app.create`](#список-параметров-fastapi_appcreate)
  - [Ключи идемпотентности:](#ключи-идемпотентности)
  - [Авторизация:](#авторизация)
    - [Авторизация с генерируемой OpenAPI схемой FastAPI](#авторизация-с-генерируемой-openapi-схемой-fastapi)
  - [Телеметрия:](#телеметрия)
  - [Обработчики ошибок:](#обработчики-ошибок)
  - [Логирование](#логирование)
    - [Список параметров `fastapi_app.logging.generate_log_config`](#список-параметров-fastapi_applogginggenerate_log_config)
  - [Kafka клиент](#kafka-клиент)
    - [Подключение к кластеру с сертификатом](#подключение-к-кластеру-с-сертификатом)
    - [Список параметров `fastapi_app.kafka.create`](#список-параметров-fastapi_appkafkacreate)
  - [Sentry:](#sentry)
  - [Метрики в формате Prometheus](#метрики-в-формате-prometheus)
    - [Пример для FastAPI](#пример-для-fastapi)
    - [Пример для Kafka consumer](#пример-для-kafka-consumer)
  - [Пагинация ответа](#пагинация-ответа)
    - [Пример пагинации ответа в роуте FastAPI](#пример-пагинации-ответа-в-роуте-fastapi)


# fastapi-app-generator

Библиотека для быстрого создания готового к использованию FastAPI приложения с
интеграцией ключевых функциональностей, таких, как:
* health-check;
* поддержка ключей идемпотентности;
* логгирование;
* админ панель;
* защита роутов с помощью API keys;
* трассировка;
* обработка ошибок;

## Быстрый старт

Для генерации FastAPI приложения воспользуйтесь функцией: `fastapi_app.create(...)`
```python
import fastapi_app
import fastapi
import uvicorn

app: fastapi.FastAPI = fastapi_app.create(
    title="Тест app",
    version="24.24.01",
    description="Пример сгенерированного приложения",
)

if __name__ == "__main__":
    uvicorn.run(app)
```

### Список параметров `fastapi_app.create`

| Аргумент                  | Тип                                                                                                                        | Описание                                                                                                              |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| *_                        |                                                                                                                            | Параметры сбора FastAPI приложения ([см. подробнее](https://fastapi.tiangolo.com/reference/fastapi/)).                |
| env_title                 | `str`                                                                                                                      | Название окружения (например: `local`, `dev`, `prod`...). Используется для генерации имен сервисов в телеметрии       |
| command_routers           | `Iterable[fastapi.APIRouter]`<br>([см. fastapi.APIRouter](https://fastapi.tiangolo.com/reference/apirouter/?h=apirouter)]) | Роутеры для команд.                                                                                                   |
| query_routers             | `Iterable[fastapi.APIRouter]`<br>([см. fastapi.APIRouter](https://fastapi.tiangolo.com/reference/apirouter/?h=apirouter)]) | Роутеры для запросов.                                                                                                 |
| healthcheck_routers       | `Iterable[fastapi.APIRouter]`<br>([см. fastapi.APIRouter](https://fastapi.tiangolo.com/reference/apirouter/?h=apirouter)]) | Health check роутеры.                                                                                                 |
| lifespan_handler          | `Lifespan[AppType]`                                                                                                        | Обработчик startup и shutdown событий. ([см. lifespan](https://fastapi.tiangolo.com/advanced/events/?h=li#lifespan)). |
| global_dependencies       | `Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]]`                                                              | Общие зависимости для приложения `FastAPI`.                                                                           |
| command_dependencies      | `Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]]`                                                              | Общие зависимости для `command_routers`.                                                                              |
| query_dependencies        | `Iterable[typing.Callable[[], typing.Awaitable[typing.Any]]]`                                                              | Общие зависимости для `query_routers`.                                                                                |
| admin_factory             | `typing.Callable[[fastapi.FastAPI], sqladmin.Admin]`                                                                       | Фабрика администрирования для создания экземпляра админа.                                                             |
| admin_views               | `Iterable[typing.Type[sqladmin.ModelView]]`                                                                                | Представления администрирования.                                                                                      |
| idempotency_require       | `bool`                                                                                                                     | Требуется ли идемпотентность.                                                                                         |
| idempotency_backed        | `base.Backend`                                                                                                             | Backend хранилища ключей идемпотентности.                                                                             |
| idempotency_enforce_uuid4 | `bool = True`                                                                                                              | Принудительно использовать UUID4 для идемпотентности.                                                                 |
| idempotency_methods       | `typing.List[typing.Text]`                                                                                                 | Список идемпотентных методов.                                                                                         |
| auth_require              | `bool`                                                                                                                     | Требуется ли аутентификация.                                                                                          |
| auth_key_pattern          | `str`                                                                                                                      | Шаблон ключа для аутентификации.                                                                                      |
| ignore_auth_methods       | `typing.List[typing.Text]`                                                                                                 | Список методов, игнорирующих аутентификацию.                                                                          |
| telemetry_enable          | `bool`                                                                                                                     | Включена ли телеметрия.                                                                                               |
| telemetry_traces_endpoint | `str`                                                                                                                      | Конечная точка для трассировки телеметрии.                                                                            |
| telemetry_traces_timeout  | `int`                                                                                                                      | Таймаут для трассировки телеметрии.                                                                                   |
| telemetry_db_engine       | `sqlalchemy.ext.asyncio.AsyncEngine`                                                                                       | Сбор телеметрии с SQLAlchemy engine.                                                                                  |
| exception_handlers        | `Iterable[ExceptionHandlerType]`                                                                                           | Набор обработчиков исключений.                                                                                        |
| sentry_enable             | `bool`                                                                                                                     | Включить поддержку sentry.                                                                                            |
| sentry_dsn                | `str`                                                                                                                      | Sentry DSN куда будут отправляться события.                                                                           |
| **kwargs                  |                                                                                                                            | Дополнительные аргументы.                                                                                             |

## Ключи идемпотентности:


```python
import fastapi_app
import fastapi
import uvicorn
import redis.asyncio as redis
from idempotency_header_middleware import backends

REDIS_CONNECTION_URL = "redis://localhost:6379/"  # заменить на свой адрес подключения

app: fastapi.FastAPI = fastapi_app.create(
    title="App с идемпотентностью",
    idempotency_require=True,  # Активация механизма идемпотентности
    idempotency_backed=backends.RedisBackend(
        redis.Redis.from_url("redis://localhost:6379/")
    ),  # устанавливаем бэкенд хранения ключей с помощью Redis
    idempotency_enforce_uuid4=True,
    idempotency_methods=["POST", "DELETE", "PUT"],  # Методы HTTP, которые будут поддерживать идемпотентность
)

if __name__ == "__main__":
    uvicorn.run(app)
```

После подключения в заголовок запросов методов с требованием к идемпотентности необходимо указать: `"Idempotency-Key": "сгенерированный_ключ"`

## Авторизация:

```python
import fastapi_app
import fastapi
import uvicorn

app: fastapi.FastAPI = fastapi_app.create(
    title="App с авторизацией",
    auth_require=True,  # Активация механизма авторизации по ключу
    auth_key_pattern="API_KEY_",  # Паттерн для поиска ключа в переменных env
    ignore_auth_methods=[
        "/health",
        "/docs",
        "/redoc",
        "/admin",
        "/openapi.json",
    ],  # Игнорирование авторизации для следующих методов.
)

if __name__ == "__main__":
    uvicorn.run(app)
```

В переменных окружения необходимо добавить ключ авторизации.
```dotenv
API_KEY_<username>=<token>
```

![img.png](docs/img.png)

### Авторизация с генерируемой OpenAPI схемой FastAPI

```python
import fastapi_app
import fastapi
import uvicorn
from fastapi_app import dependencies


auth_dependency = fastapi.Depends(
    dependencies.api_key.ValidateAPIKeyHeader(
        header_name="x-api-key",
        api_keys=dependencies.api_key.get_api_keys_from_env(
            api_auth_key_prefix="API_KEY"
        ),
    )
)

app: fastapi.FastAPI = fastapi_app.create(
    title="App с авторизацией и openapi схемой",
    global_dependencies=[auth_dependency],
)


@app.get("hello")
def abeba():
    return "hello"


if __name__ == "__main__":
    uvicorn.run(app)

```

## Телеметрия:

Для подключения телеметрии необходимо запустить или иметь доступ к Jagger.
<br/>Телеметрия собирается с:
* redis
* sqlalchemy
* logging
* httpx
* fastapi

```python
import fastapi_app
import fastapi
import uvicorn

DB_CONNECTION_URL = "mysql+asyncmy://localhost:3306/test"  # заменить на свой адрес подключения к БД

app: fastapi.FastAPI = fastapi_app.create(
    title="App с телеметрией",
    env_title="dev",  # название окружения, для распознавания трассировок между разными окружениями приложения.
    telemetry_enable=True,  # Активация сбора телеметрии
    telemetry_traces_endpoint="http://localhost:4318/v1/traces",  # складывает трассировку с Jagger по указанному пути
    db_connection_url=DB_CONNECTION_URL  # трассировка запросов к БД
)

if __name__ == "__main__":
    uvicorn.run(app)
```

## Обработчики ошибок:

Чтобы использовать [кастомные обработчики ошибок для FastAPI](https://fastapi.tiangolo.com/tutorial/handling-errors/?h=exce#install-custom-exception-handlers), можно воспользоваться декоратором [fastapi_app.exception_handlers.bind_exception](https://gitlab.timeweb.net/finance/billing/fastapi-app/-/blob/DEV-3817-dev/fastapi_app/exception_handlers/exceptions.py#L29).
<br/>Пример:
```python
import fastapi_app
import fastapi
import uvicorn
from fastapi_app import exception_handlers
from fastapi import status, requests

class AlreadyExists(Exception):
    message: str

    def __init__(self, message: str = ""):
        self.message = message


# Объявления статус кода и ответа на ошибку AlreadyExists
@exception_handlers.bind_exception(status_code=status.HTTP_409_CONFLICT)
def already_exists_handler(_: requests.Request, error: AlreadyExists) -> dict[str, str]:
    return {"error": error.message}


app: fastapi.FastAPI = fastapi_app.create(
    title="App с авторизацией",
    exception_handlers=[already_exists_handler]  # подключаем кастомные обработчики ошибок для FastAPI приложения.
)

if __name__ == "__main__":
    uvicorn.run(app)
```

Для объявления в OpenAPI ответов кастомных обработчиков ошибок роутера необходимо связать их с `responses` при помощи `fastapi_app.exception_handlers`:
```python
import fastapi_app
import fastapi
from fastapi_app import exception_handlers
from fastapi import status, requests


class AlreadyExists(Exception):
    message: str

    def __init__(self, message: str = ""):
        self.message = message


@exception_handlers.bind_exception(status_code=status.HTTP_409_CONFLICT)
def already_exists_handler(_: requests.Request, error: AlreadyExists) -> dict[str, str]:
    return {"error": error.message}


router = fastapi.APIRouter(
    responses=exception_handlers.get_exception_responses(AlreadyExists,),  # Объявления в OpenAPI ответов кастомных обработчиков ошибок роутера
)

app: fastapi.FastAPI = fastapi_app.create(
    title="App с авторизацией",
    command_routers=[router],
    exception_handlers=[already_exists_handler]  # подключаем кастомные обработчики ошибок для FastAPI приложения.
)
```

# Логирование

Для получения настроек конфигурации логирования - воспользуйтесь методом `fastapi_app.logging.generate_log_config`
```python
import fastapi_app
import fastapi
import uvicorn
from fastapi_app import logging
from logging import config as logging_config

title = "Тест app"
version = "24.24.01"

# Генерация конфигурации предустановленного формата логирования
log_config = fastapi_app.logging.generate_log_config(
    logging_level="INFO",
    serialize=True,
    app_name=title,
    app_version=version
)

logging_config.dictConfig(log_config)

app: fastapi.FastAPI = fastapi_app.create(
    title=title,
    version=version,
    description="Пример сгенерированного приложения",
)

if __name__ == "__main__":
    uvicorn.run(app)

```
### Список параметров `fastapi_app.logging.generate_log_config`

| Аргумент      | Тип    | Описание                                                                        |
| ------------- | ------ | ------------------------------------------------------------------------------- |
| logging_level | `str`  | Уровень логирования: `NOTSET`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| serialize     | `bool` | Сериализация лога в JSON.                                                       |
| app_name      | `str`  | Название приложения.                                                            |
| app_version   | `str`  | Версия приложения.                                                              |

## Kafka клиент

Чтобы сгенерировать клиента Kafka, воспользуйтесь `fastapi_app.kafka.create(...)`:

```python
from fastapi_app import kafka

app = kafka.create(
    app_title="Test consumer",
    env_title="test",
    dsn="localhost:3384",
    security_protocol="SASL_PLAINTEXT",
    sasl_mechanism="PLAIN",
    user="",
    password="",
    max_wait_ms=10,
    group_id="test",
    topics=["topic_"],
    telemetry_enable=False,
)
```

### Подключение к кластеру с сертификатом

```
    context = create_ssl_context(cafile="/path/to/ca.crt")

    consumer = bootstrap.create(
        app_title="Test consumer",
        env_title="test",
        dsn=",".join(
            [
                "kafka-dev-1:9493",
                "kafka-dev-2:9493",
                "kafka-dev-3:9493",
            ]
        ),
        topics=["topic_1"],
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-256",
        user="test-user",
        password="test-pwd",
        max_wait_ms=10 * 1000,
        group_id="test-connection-group",
        ssl_context=context,
    )
```

### Список параметров `fastapi_app.kafka.create`

| Аргумент                  | Тип                                  | Описание                                                                                                        |
| ------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| app_title                 | `str`                                | Название приложения                                                                                             |
| env_title                 | `str`                                | Название окружения (например: `local`, `dev`, `prod`...). Используется для генерации имен сервисов в телеметрии |
| dsn                       | `str`                                | Хост:порт на подключение к Kafka                                                                                |
| security_protocol         | `str`                                | Протокол безопасности                                                                                           |
| sasl_mechanism            | `str`                                | Механизм протокола `SASL`                                                                                       |
| user                      | `str`                                | Логин пользователя Kafka                                                                                        |
| password                  | `str`                                | Пароль пользователя kafka                                                                                       |
| max_wait_ms               | `int`                                | Максимальное время ожидания ответа в мс                                                                         |
| group_id                  | `str`                                | ID группы                                                                                                       |
| topics                    | `str`                                | Префикс читаемых топиков                                                                                        |
| telemetry_enable          | `bool`                               | Включена ли телеметрия.                                                                                         |
| telemetry_traces_endpoint | `str`                                | Конечная точка для трассировки телеметрии.                                                                      |
| telemetry_traces_timeout  | `int`                                | Таймаут для трассировки телеметрии.                                                                             |
| telemetry_db_engine       | `sqlalchemy.ext.asyncio.AsyncEngine` | Сбор телеметрии с SQLAlchemy engine.                                                                            |
| sentry_enable             | `bool`                               | DEPRECATED. Использовать `telemetry.sentry:configure_sentry`. Включить поддержку sentry.                        |
| sentry_dsn                | `str`                                | DEPRECATED. Использовать `telemetry.sentry:configure_sentry`. Sentry DSN куда будут отправляться события.       |
| ssl_context               | `ssl.SSLContext`                     | SSL контекст                                                                                                    |

## Sentry:

Для интеграции с `sentry` необходимо указать DSN, куда будут отправляться события.


### Пример для FastAPI
```python
import fastapi_app
import fastapi
import uvicorn
from fastapi_app.telemetry import sentry

sentry_enabled = True
sentry_dsn = "https://examplePublicKey@o0.ingest.sentry.io/0"
if sentry_enabled:
    sentry.configure_sentry(sentry_dsn)

app: fastapi.FastAPI = fastapi_app.create(
    title="App с телеметрией",
    env_title="dev",  # название окружения, для распознавания трассировок между разными окружениями приложения.
)

if __name__ == "__main__":
    uvicorn.run(app)
```

### Пример для Kafka consumer
```python
from fastapi_app import kafka
from fastapi_app.telemetry import sentry

sentry_enabled = True
sentry_dsn = "https://examplePublicKey@o0.ingest.sentry.io/0"
if sentry_enabled:
    sentry.configure_sentry(sentry_dsn)

app: kafka.KafkaConsumer = kafka.create(
    ...,  # Прочие параметры настроек для Kafka consumer
)

app.consume(on_message=on_update_message)
```

## Пагинация ответа

Для создания пагинации ответов в FastAPI можно воспользоваться классом `fastapi_app.paginator.PaginatedResult`.

### Пример пагинации ответа в роуте FastAPI

```python
import fastapi_app
import fastapi
from fastapi_app import paginator

app = fastapi_app.create(
    title="Test",
    debug=True,
    description="Pagination test API",
)


# Базовая пагинация ответа
@app.get("/test_paginate", response_model=paginator.PaginatedResult[int])
async def test_pagination_route(request: fastapi.Request, page: int = 1, limit: int = 25):
    total = [i for i in range(limit * 10)]
    offset = limit * (page - 1)
    return paginator.PaginatedResult[int](
        current_page=page,
        total=len(total),
        data=total[offset:offset + limit],
        limit=limit,
        url=str(request.url)
    )
```
