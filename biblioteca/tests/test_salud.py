"""Pruebas del endpoint de salud."""


def test_salud_responde_ok(cliente):
    respuesta = cliente.get("/api/v1/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "database": "ok"}


def test_salud_incluye_request_id(cliente):
    respuesta = cliente.get("/api/v1/health")

    assert "X-Request-ID" in respuesta.headers
