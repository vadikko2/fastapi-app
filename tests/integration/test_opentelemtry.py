from fastapi import status


async def test_tracing(api_with_telemetry, span_exporter):
    """Проверка отправки трассировок"""
    response = await api_with_telemetry.get("/test")

    spans = span_exporter.get_finished_spans()

    assert response.status_code == status.HTTP_200_OK
    assert len(spans) > 0
    assert spans[-1].name == "GET /test"
    assert spans[-1].status.is_ok
    assert spans[-1].attributes["http.status_code"] == status.HTTP_200_OK
