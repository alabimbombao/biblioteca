"""Pruebas de la matriz de permisos por rol."""

from tests.conftest import cabecera


def _libro_json(autor, categoria, isbn="9788437604961"):
    return {
        "titulo": "Cien Anos De Soledad",
        "isbn": isbn,
        "anio_publicacion": 1967,
        "ejemplares": 2,
        "autor_id": autor.id,
        "categoria_ids": [categoria.id],
    }


def test_catalogo_publico_sin_token(cliente, catalogo):
    assert cliente.get("/api/v1/libros").status_code == 200
    assert cliente.get("/api/v1/autores").status_code == 200
    assert cliente.get("/api/v1/categorias").status_code == 200


def test_endpoint_protegido_sin_token(cliente, catalogo):
    autor, categoria, libro = catalogo

    respuesta = cliente.post(
        "/api/v1/libros", json=_libro_json(autor, categoria)
    )

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_socio_no_puede_crear_libro(cliente, catalogo, ana):
    autor, categoria, libro = catalogo

    respuesta = cliente.post(
        "/api/v1/libros",
        json=_libro_json(autor, categoria),
        headers=cabecera(ana),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "No tiene permisos para esta acción"


def test_bibliotecario_crea_libro(cliente, catalogo, bibliotecario):
    autor, categoria, libro = catalogo

    respuesta = cliente.post(
        "/api/v1/libros",
        json=_libro_json(autor, categoria),
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 201


def test_bibliotecario_no_puede_borrar(cliente, catalogo, bibliotecario):
    autor, categoria, libro = catalogo

    respuesta = cliente.delete(
        f"/api/v1/libros/{libro.id}",
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 403


def test_admin_puede_borrar_libro(cliente, catalogo, admin):
    autor, categoria, libro = catalogo

    respuesta = cliente.delete(
        f"/api/v1/libros/{libro.id}",
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 204


def test_reportes_solo_staff(cliente, ana, bibliotecario):
    negado = cliente.get(
        "/api/v1/reportes/resumen", headers=cabecera(ana)
    )
    permitido = cliente.get(
        "/api/v1/reportes/resumen", headers=cabecera(bibliotecario)
    )

    assert negado.status_code == 403
    assert permitido.status_code == 200


def test_usuarios_solo_admin(cliente, ana, bibliotecario, admin):
    assert (
        cliente.get("/api/v1/usuarios", headers=cabecera(ana)).status_code
        == 403
    )
    assert (
        cliente.get(
            "/api/v1/usuarios", headers=cabecera(bibliotecario)
        ).status_code
        == 403
    )
    assert (
        cliente.get("/api/v1/usuarios", headers=cabecera(admin)).status_code
        == 200
    )


def test_socios_me_solo_para_socios(cliente, admin, ana):
    assert (
        cliente.get("/api/v1/socios/me", headers=cabecera(admin)).status_code
        == 403
    )
    assert (
        cliente.get("/api/v1/socios/me", headers=cabecera(ana)).status_code
        == 200
    )


def test_listar_socios_requiere_staff(cliente, ana, bibliotecario):
    assert (
        cliente.get("/api/v1/socios", headers=cabecera(ana)).status_code
        == 403
    )
    assert (
        cliente.get(
            "/api/v1/socios", headers=cabecera(bibliotecario)
        ).status_code
        == 200
    )


def test_prestamos_requieren_autenticacion(cliente):
    assert cliente.get("/api/v1/prestamos").status_code == 401
