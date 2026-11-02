"""Pruebas de administración de usuarios."""

from tests.conftest import cabecera


def test_listar_usuarios_y_filtros(cliente, admin, bibliotecario, ana):
    listado = cliente.get("/api/v1/usuarios", headers=cabecera(admin))
    assert listado.status_code == 200
    assert listado.json()["total"] == 3

    solo_admin = cliente.get(
        "/api/v1/usuarios",
        params={"rol": "admin"},
        headers=cabecera(admin),
    )
    assert solo_admin.json()["total"] == 1

    inactivos = cliente.get(
        "/api/v1/usuarios",
        params={"activo": False},
        headers=cabecera(admin),
    )
    assert inactivos.json()["total"] == 0


def test_admin_crea_bibliotecario(cliente, admin):
    datos = {
        "email": "nuevo@biblioteca.com",
        "nombre": "Nuevo Biblio",
        "password": "Nuevo1234",
        "rol": "bibliotecario",
    }

    creado = cliente.post(
        "/api/v1/usuarios", json=datos, headers=cabecera(admin)
    )
    assert creado.status_code == 201
    assert creado.json()["rol"] == "bibliotecario"
    assert "password_hash" not in creado.json()

    duplicado = cliente.post(
        "/api/v1/usuarios", json=datos, headers=cabecera(admin)
    )
    assert duplicado.status_code == 409


def test_no_se_puede_crear_socio_desde_usuarios(cliente, admin):
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json={
            "email": "socio@biblioteca.com",
            "nombre": "Socio Nuevo",
            "password": "Socio1234",
            "rol": "socio",
        },
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 422


def test_cambiar_rol(cliente, admin, bibliotecario):
    respuesta = cliente.patch(
        f"/api/v1/usuarios/{bibliotecario.id}/rol",
        json={"rol": "socio"},
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "socio"


def test_desactivar_usuario_revoca_sus_tokens(cliente, admin, bibliotecario):
    login = cliente.post(
        "/api/v1/auth/login",
        data={"username": "biblio@biblioteca.com", "password": "Biblio1234"},
    ).json()

    desactivado = cliente.patch(
        f"/api/v1/usuarios/{bibliotecario.id}/activo",
        json={"activo": False},
        headers=cabecera(admin),
    )
    assert desactivado.status_code == 200
    assert desactivado.json()["activo"] is False

    me = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert me.status_code == 403

    refresh = cliente.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refresh.status_code == 401


def test_reactivar_usuario(cliente, admin, bibliotecario):
    cliente.patch(
        f"/api/v1/usuarios/{bibliotecario.id}/activo",
        json={"activo": False},
        headers=cabecera(admin),
    )

    respuesta = cliente.patch(
        f"/api/v1/usuarios/{bibliotecario.id}/activo",
        json={"activo": True},
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is True


def test_admin_no_puede_quitarse_su_rol(cliente, admin):
    respuesta = cliente.patch(
        f"/api/v1/usuarios/{admin.id}/rol",
        json={"rol": "socio"},
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 422


def test_admin_no_puede_desactivarse(cliente, admin):
    respuesta = cliente.patch(
        f"/api/v1/usuarios/{admin.id}/activo",
        json={"activo": False},
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 422


def test_usuario_inexistente(cliente, admin):
    respuesta = cliente.patch(
        "/api/v1/usuarios/99999/rol",
        json={"rol": "socio"},
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 404
