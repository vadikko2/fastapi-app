import functools
import typing

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http import trace_exporter
    from opentelemetry.sdk import trace as sdk_trace
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import export

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    # opentelemetry is optional dependency
    OPENTELEMETRY_AVAILABLE = False
    # Create dummy types to avoid errors
    trace = None  # type: ignore
    trace_exporter = None  # type: ignore
    sdk_trace = None  # type: ignore
    SERVICE_NAME = None  # type: ignore
    Resource = None  # type: ignore
    export = None  # type: ignore

__all__ = ("init_tracer",)


IGNORED_SPAN_NAME = "IGNORED_SPAN"


def ignore_traces(func):
    if not OPENTELEMETRY_AVAILABLE:
        return func  # Return function as-is if opentelemetry is not available

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(IGNORED_SPAN_NAME):
            return await func(*args, **kwargs)

    return wrapper


if OPENTELEMETRY_AVAILABLE:

    class SpanFilteringProcessor(export.BatchSpanProcessor):
        """"""

        def on_start(
            self,
            span: export.Span,
            parent_context: typing.Optional[export.Context] = None,
        ) -> None:
            # Проверяем если span необходимо пропустить
            if span.name == IGNORED_SPAN_NAME:
                # Создаем новый контекст span'а со следующими свойствами:
                #   * trace_id такой же, как trace_id исходного span'а.
                #   * span_id такой же, как span_id исходного span'а.
                #   * is_remote установлено значение `False`.
                #   * trace_flags `DEFAULT`.
                #   * trace_state такой же, как trace_state исходного span'а.
                span._context = trace.SpanContext(
                    span.context.trace_id,
                    span.context.span_id,
                    span.context.is_remote,
                    trace.TraceFlags(trace.TraceFlags.DEFAULT),
                    span.context.trace_state,
                )
else:
    # Dummy class if opentelemetry is not available
    class SpanFilteringProcessor:  # type: ignore
        pass


def init_tracer(
    service_name: str,
    timeout: int = 10,
    endpoint: str = "http://localhost:4318/v1/traces",
) -> typing.Any:
    if not OPENTELEMETRY_AVAILABLE:
        raise ImportError(
            "opentelemetry is not installed. "
            "Install it with: pip install 'fastapi-app[otlp]' or 'fastapi-app[all]'",
        )

    resource = Resource.create({SERVICE_NAME: service_name})
    tracer_provider = sdk_trace.TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(
        SpanFilteringProcessor(
            trace_exporter.OTLPSpanExporter(
                endpoint=endpoint,
                timeout=timeout,
            ),
        ),
    )

    return tracer_provider
