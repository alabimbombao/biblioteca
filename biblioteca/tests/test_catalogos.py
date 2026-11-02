"""Pruebas de los CRUD del catálogo."""

from tests.conftest import cabecera


def _libro_json(autor, categoria, isbn="9788437604947"):
    return {
        "titulo": "Cien Anos De Soledad",
        "isbn": isbn,
        "anio_publicacion": 1967,
        "ejemplares": 2,
        "autor_id": autor.id,
        "categoria_ids": [categoria.id],
    }


def test_listar_autores_paginado(cliente, catalogo):
    respuesta = cliente.get("/api/v1/autores")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"items", "total", "skip", "limit"}
    assert cuerpo["total"] == 1
    assert cuerpo["skip"] == 0
    assert cuerpo["limit"] == 10


def test_crud_autores(cliente, bibliotecario, admin):
    creado = cliente.post(
        "/api/v1/autores",
        json={
            "nombre": "isabel allende",
            "nacionalidad": "Chilena",
            "anio_nacimiento": 1942,
        },
        headers=cabecera(bibliotecario),
    )
    assert creado.status_code == 201
    autor = creado.json()
    assert autor["nombre"] == "Isabel Allende"

    duplicado = cliente.post(
        "/api/v1/autores",
        json={"nombre": "Isabel Allende"},
        headers=cabecera(bibliotecario),
    )
    assert duplicado.status_code == 409

    obtenido = cliente.get(f"/api/v1/autores/{autor['id']}")
    assert obtenido.status_code == 200

    actualizado = cliente.patch(
        f"/api/v1/autores/{autor['id']}",
        json={"nacionalidad": "Chilena"},
        headers=cabecera(bibliotecario),
    )
    assert actualizado.status_code == 200

    eliminado = cliente.delete(
        f"/api/v1/autores/{autor['id']}",
        headers=cabecera(admin),
    )
    assert eliminado.status_code == 204

    inexistente = cliente.get(f"/api/v1/autores/{autor['id']}")
    assert inexistente.status_code == 404


def test_crud_categorias(cliente, bibliotecario, admin):
    creada = cliente.post(
        "/api/v1/categorias",
        json={"nombre": "poesia", "descripcion": "Poemas"},
        headers=cabecera(bibliotecario),
    )
    assert creada.status_code == 201
    categoria = creada.json()

    listado = cliente.get("/api/v1/categorias")
    assert listado.status_code == 200
    assert listado.json()["total"] == 1

    duplicada = cliente.post(
        "/api/v1/categorias",
        json={"nombre": "poesia"},
        headers=cabecera(bibliotecario),
    )
    assert duplicada.status_code == 409

    actualizada = cliente.patch(
        f"/api/v1/categorias/{categoria['id']}",
        json={"descripcion": "Poesia latinoamericana"},
        headers=cabecera(bibliotecario),
    )
    assert actualizada.status_code == 200

    eliminada = cliente.delete(
        f"/api/v1/categorias/{categoria['id']}",
        headers=cabecera(admin),
    )
    assert eliminada.status_code == 204


def test_listar_libros_con_filtros(cliente, catalogo):
    autor, categoria, libro = catalogo

    respuesta = cliente.get(
        "/api/v1/libros",
        params={"buscar": "cien", "categoria_id": categoria.id},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["isbn"] == libro.isbn
    assert cuerpo["items"][0]["disponibles"] == 2

    por_autor = cliente.get(
        "/api/v1/libros", params={"autor": "garcia"}
    )
    assert por_autor.status_code == 200
    assert por_autor.json()["total"] == 1

    por_anio = cliente.get(
        "/api/v1/libros", params={"desde": 1900, "hasta": 2000}
    )
    assert por_anio.status_code == 200
    assert por_anio.json()["total"] == 1

    ordenados = cliente.get(
        "/api/v1/libros", params={"orden": "anio"}
    )
    assert ordenados.status_code == 200


def test_crear_y_actualizar_libro(cliente, catalogo, bibliotecario, admin):
    autor, categoria, libro = catalogo
    datos = _libro_json(autor, categoria, isbn="9788437604947")

    creado = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=cabecera(bibliotecario),
    )
    assert creado.status_code == 201
    nuevo = creado.json()
    assert nuevo["autor"]["id"] == autor.id
    assert len(nuevo["categorias"]) == 1

    duplicado = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=cabecera(bibliotecario),
    )
    assert duplicado.status_code == 409

    actualizado = cliente.patch(
        f"/api/v1/libros/{nuevo['id']}",
        json={"ejemplares": 3},
        headers=cabecera(bibliotecario),
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["ejemplares"] == 3

    de_autor = cliente.get(f"/api/v1/autores/{autor.id}/libros")
    assert de_autor.status_code == 200
    assert de_autor.json()["total"] == 2

    eliminado = cliente.delete(
        f"/api/v1/libros/{nuevo['id']}",
        headers=cabecera(admin),
    )
    assert eliminado.status_code == 204

    inexistente = cliente.get(f"/api/v1/libros/{nuevo['id']}")
    assert inexistente.status_code == 404


def test_crear_libro_con_autor_inexistente(cliente, catalogo, bibliotecario):
    autor, categoria, libro = catalogo
    datos = _libro_json(autor, categoria)
    datos["autor_id"] = 99999

    respuesta = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 404


def test_crear_libro_con_categoria_inexistente(
    cliente, catalogo, bibliotecario
):
    autor, categoria, libro = catalogo
    datos = _libro_json(autor, categoria, isbn="9788437604954")
    datos["categoria_ids"] = [99999]

    respuesta = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 404


def test_eliminar_autor_con_libros(cliente, catalogo, admin):
    autor, categoria, libro = catalogo

    respuesta = cliente.delete(
        f"/api/v1/autores/{autor.id}",
        headers=cabecera(admin),
    )

    assert respuesta.status_code == 409
