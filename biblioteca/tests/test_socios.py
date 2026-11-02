"""Pruebas de socios y del perfil propio."""

from tests.conftest import cabecera


def test_perfil_propio(cliente, ana):
    respuesta = cliente.get("/api/v1/socios/me", headers=cabecera(ana))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "ana@example.com"
    assert "password_hash" not in cuerpo


def test_socio_no_puede_cambiar_su_estado(cliente, ana):
    respuesta = cliente.patch(
        "/api/v1/socios/me",
        json={"activo": False},
        headers=cabecera(ana),
    )

    assert respuesta.status_code == 422


def test_socio_actualiza_su_nombre_y_telefono(cliente, ana):
    respuesta = cliente.patch(
        "/api/v1/socios/me",
        json={"nombre": "ana maria torres", "telefono": "3001234567"},
        headers=cabecera(ana),
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Ana Maria Torres"
    assert cuerpo["telefono"] == "3001234567"


def test_mis_prestamos_y_mis_multas_vacios(cliente, ana):
    prestamos = cliente.get(
        "/api/v1/socios/me/prestamos", headers=cabecera(ana)
    )
    multas = cliente.get(
        "/api/v1/socios/me/multas", headers=cabecera(ana)
    )

    assert prestamos.status_code == 200
    assert prestamos.json()["total"] == 0
    assert multas.status_code == 200
    assert multas.json()["items"] == []
    assert float(multas.json()["total_adeudado"]) == 0.0


def test_listar_socios_con_filtro(cliente, ana, luis, bibliotecario):
    respuesta = cliente.get(
        "/api/v1/socios",
        params={"activo": True},
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2


def test_crear_socio_y_duplicado(cliente, bibliotecario):
    datos = {
        "nombre": "Carlos Ruiz",
        "email": "carlos@example.com",
        "telefono": "3101234567",
    }

    creado = cliente.post(
        "/api/v1/socios",
        json=datos,
        headers=cabecera(bibliotecario),
    )
    assert creado.status_code == 201

    duplicado = cliente.post(
        "/api/v1/socios",
        json=datos,
        headers=cabecera(bibliotecario),
    )
    assert duplicado.status_code == 409


def test_staff_consulta_y_actualiza_socio(
    cliente, ana, bibliotecario
):
    socio_id = ana.socio_id

    obtenido = cliente.get(
        f"/api/v1/socios/{socio_id}", headers=cabecera(bibliotecario)
    )
    assert obtenido.status_code == 200

    actualizado = cliente.patch(
        f"/api/v1/socios/{socio_id}",
        json={"telefono": "3201234567"},
        headers=cabecera(bibliotecario),
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["telefono"] == "3201234567"


def test_admin_desactiva_socio_con_usuario(cliente, ana, admin):
    socio_id = ana.socio_id

    eliminado = cliente.delete(
        f"/api/v1/socios/{socio_id}", headers=cabecera(admin)
    )
    assert eliminado.status_code == 204

    consultado = cliente.get(
        f"/api/v1/socios/{socio_id}", headers=cabecera(admin)
    )
    assert consultado.status_code == 200
    assert consultado.json()["activo"] is False


def test_admin_elimina_socio_sin_historial(cliente, admin):
    creado = cliente.post(
        "/api/v1/socios",
        json={"nombre": "Temporal Uno", "email": "temporal@example.com"},
        headers=cabecera(admin),
    ).json()

    eliminado = cliente.delete(
        f"/api/v1/socios/{creado['id']}", headers=cabecera(admin)
    )
    assert eliminado.status_code == 204

    inexistente = cliente.get(
        f"/api/v1/socios/{creado['id']}", headers=cabecera(admin)
    )
    assert inexistente.status_code == 404
