"""Pruebas de préstamos, devoluciones y multas."""

from datetime import date, timedelta
from decimal import Decimal

from app.models.libro import Libro
from tests.conftest import cabecera, crear_socio


def prestar(
    cliente,
    usuario,
    socio,
    libro,
    dias=14,
    fecha_prestamo=None,
):
    """Registra un préstamo a través de la API."""
    datos = {
        "socio_id": socio.id,
        "libro_id": libro.id,
        "dias": dias,
    }
    if fecha_prestamo is not None:
        datos["fecha_prestamo"] = fecha_prestamo.isoformat()

    return cliente.post(
        "/api/v1/prestamos",
        json=datos,
        headers=cabecera(usuario),
    )


def devolver(cliente, usuario, prestamo_id, fecha=None):
    """Registra una devolución a través de la API."""
    datos = {}
    if fecha is not None:
        datos["fecha_devolucion"] = fecha.isoformat()

    return cliente.post(
        f"/api/v1/prestamos/{prestamo_id}/devolucion",
        json=datos,
        headers=cabecera(usuario),
    )


def _nuevo_libro(db, autor, categoria, isbn):
    libro = Libro(
        titulo=f"Libro {isbn}",
        isbn=isbn,
        anio_publicacion=2000,
        ejemplares=1,
        autor_id=autor.id,
    )
    libro.categorias = [categoria]
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return libro


def test_registrar_prestamo_guarda_quien_lo_registro(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo

    respuesta = prestar(
        cliente, bibliotecario, ana, libro
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["socio_id"] == ana.socio_id
    assert cuerpo["registrado_por_id"] == bibliotecario.id
    assert cuerpo["estado"] == "activo"
    assert cuerpo["multa_pagada"] is True


def test_socio_solo_ve_sus_prestamos(
    cliente, catalogo, ana, luis, bibliotecario
):
    autor, categoria, libro = catalogo
    propio = prestar(cliente, bibliotecario, ana, libro).json()
    ajeno = prestar(cliente, bibliotecario, luis, libro).json()

    listado = cliente.get(
        "/api/v1/prestamos", headers=cabecera(ana)
    )
    assert listado.status_code == 200
    assert listado.json()["total"] == 1
    assert listado.json()["items"][0]["id"] == propio["id"]

    filtrado = cliente.get(
        "/api/v1/prestamos",
        params={"socio_id": luis.socio_id},
        headers=cabecera(ana),
    )
    assert filtrado.json()["total"] == 1
    assert filtrado.json()["items"][0]["id"] == propio["id"]

    negado = cliente.get(
        f"/api/v1/prestamos/{ajeno['id']}", headers=cabecera(ana)
    )
    assert negado.status_code == 404

    permitido = cliente.get(
        f"/api/v1/prestamos/{propio['id']}", headers=cabecera(ana)
    )
    assert permitido.status_code == 200


def test_staff_ve_todos_los_prestamos(
    cliente, catalogo, ana, luis, bibliotecario
):
    autor, categoria, libro = catalogo
    prestar(cliente, bibliotecario, ana, libro)
    prestar(cliente, bibliotecario, luis, libro)

    respuesta = cliente.get(
        "/api/v1/prestamos", headers=cabecera(bibliotecario)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2


def test_devolucion_sin_multa(cliente, catalogo, ana, bibliotecario):
    autor, categoria, libro = catalogo
    prestamo = prestar(cliente, bibliotecario, ana, libro).json()

    respuesta = devolver(
        cliente, bibliotecario, prestamo["id"]
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "devuelto"
    assert Decimal(str(cuerpo["multa"])) == Decimal("0")
    assert cuerpo["multa_pagada"] is True


def test_devolucion_repetida(cliente, catalogo, ana, bibliotecario):
    autor, categoria, libro = catalogo
    prestamo = prestar(cliente, bibliotecario, ana, libro).json()
    devolver(cliente, bibliotecario, prestamo["id"])

    respuesta = devolver(cliente, bibliotecario, prestamo["id"])

    assert respuesta.status_code == 409


def test_prestamo_duplicado_sin_devolver(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestar(cliente, bibliotecario, ana, libro)

    respuesta = prestar(cliente, bibliotecario, ana, libro)

    assert respuesta.status_code == 409


def test_sin_ejemplares_disponibles(
    cliente, db, catalogo, ana, luis, bibliotecario
):
    autor, categoria, libro = catalogo
    libro.ejemplares = 1
    db.commit()

    assert prestar(cliente, bibliotecario, ana, libro).status_code == 201

    respuesta = prestar(cliente, bibliotecario, luis, libro)
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "No hay ejemplares disponibles"


def test_socio_inactivo_no_puede_pedir_prestamo(
    cliente, db, catalogo, bibliotecario
):
    autor, categoria, libro = catalogo
    inactivo = crear_socio(
        db,
        nombre="Inactivo Uno",
        email="inactivo@example.com",
        activo=False,
    )

    respuesta = prestar(cliente, bibliotecario, inactivo, libro)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "El socio no esta activo"


def test_multas_pendientes_bloquean_nuevos_prestamos(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    hace_20_dias = date.today() - timedelta(days=20)

    prestamo = prestar(
        cliente,
        bibliotecario,
        ana,
        libro,
        dias=7,
        fecha_prestamo=hace_20_dias,
    ).json()

    devuelto = devolver(cliente, bibliotecario, prestamo["id"])
    assert devuelto.status_code == 200
    assert Decimal(str(devuelto.json()["multa"])) == Decimal("6.5")
    assert devuelto.json()["multa_pagada"] is False

    bloqueado = prestar(cliente, bibliotecario, ana, libro)
    assert bloqueado.status_code == 422
    assert bloqueado.json()["detail"] == "El socio tiene multas pendientes"

    multas = cliente.get(
        "/api/v1/socios/me/multas", headers=cabecera(ana)
    )
    assert multas.status_code == 200
    assert len(multas.json()["items"]) == 1
    assert Decimal(str(multas.json()["total_adeudado"])) == Decimal("6.5")

    pago = cliente.post(
        f"/api/v1/prestamos/{prestamo['id']}/pago-multa",
        headers=cabecera(bibliotecario),
    )
    assert pago.status_code == 200
    assert pago.json()["multa_pagada"] is True

    permitido = prestar(cliente, bibliotecario, ana, libro)
    assert permitido.status_code == 201


def test_pago_de_multa_repetido(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestamo = prestar(
        cliente,
        bibliotecario,
        ana,
        libro,
        dias=7,
        fecha_prestamo=date.today() - timedelta(days=20),
    ).json()
    devolver(cliente, bibliotecario, prestamo["id"])

    primero = cliente.post(
        f"/api/v1/prestamos/{prestamo['id']}/pago-multa",
        headers=cabecera(bibliotecario),
    )
    segundo = cliente.post(
        f"/api/v1/prestamos/{prestamo['id']}/pago-multa",
        headers=cabecera(bibliotecario),
    )

    assert primero.status_code == 200
    assert segundo.status_code == 409


def test_pago_de_multa_sin_multa(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestamo = prestar(cliente, bibliotecario, ana, libro).json()

    respuesta = cliente.post(
        f"/api/v1/prestamos/{prestamo['id']}/pago-multa",
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 409


def test_pago_de_multa_inexistente(cliente, bibliotecario):
    respuesta = cliente.post(
        "/api/v1/prestamos/99999/pago-multa",
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 404


def test_prestamos_vencidos_bloquean_nuevos(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestar(
        cliente,
        bibliotecario,
        ana,
        libro,
        dias=7,
        fecha_prestamo=date.today() - timedelta(days=20),
    )

    respuesta = prestar(cliente, bibliotecario, ana, libro)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "El socio tiene prestamos vencidos"


def test_maximo_tres_prestamos(
    cliente, db, catalogo, ana, bibliotecario
):
    autor, categoria, primer_libro = catalogo
    libros = [primer_libro]
    for indice in range(3):
        libros.append(
            _nuevo_libro(
                db,
                autor,
                categoria,
                isbn=f"97800000000{indice + 1:02d}",
            )
        )

    for libro in libros[:3]:
        assert prestar(cliente, bibliotecario, ana, libro).status_code == 201

    respuesta = prestar(cliente, bibliotecario, ana, libros[3])
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Maximo de 3 prestamos"


def test_devolucion_anterior_al_prestamo(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestamo = prestar(cliente, bibliotecario, ana, libro).json()

    respuesta = devolver(
        cliente,
        bibliotecario,
        prestamo["id"],
        fecha=date.today() - timedelta(days=5),
    )

    assert respuesta.status_code == 422


def test_prestamos_de_un_socio_para_staff(
    cliente, catalogo, ana, bibliotecario
):
    autor, categoria, libro = catalogo
    prestar(cliente, bibliotecario, ana, libro)

    respuesta = cliente.get(
        f"/api/v1/socios/{ana.socio_id}/prestamos",
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1


def test_prestamo_a_socio_inexistente(cliente, catalogo, bibliotecario):
    autor, categoria, libro = catalogo

    respuesta = cliente.post(
        "/api/v1/prestamos",
        json={"socio_id": 99999, "libro_id": libro.id, "dias": 7},
        headers=cabecera(bibliotecario),
    )

    assert respuesta.status_code == 404
