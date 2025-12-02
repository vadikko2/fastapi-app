try:
    from fastapi_app.telemetry.telemetry import init_tracer

    __all__ = ("init_tracer",)
except ImportError:
    # opentelemetry is optional dependency
    __all__ = ()
