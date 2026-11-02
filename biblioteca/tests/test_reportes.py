"""Pruebas de los reportes del Taller 1."""

from datetime import date, timedelta

from tests.conftest import cabecera
from tests.test_prestamos import devolver, prestar


def test_reportes_completos(
    cliente, catalogo, ana, luis, bibliotecario
):
    autor, categoria, libro = catalogo
    cabecera_staff = cabecera(bibliotecario)

    # Préstamo devuelto a tiempo.
    a_tiempo = prestar(cliente, bibliotecario, ana, libro).json()
    devolver(cliente, bibliotecario, a_tiempo["id"])

    # Préstamo devuelto con retraso y multa pagada.
    con_retraso = prestar(
        cliente,
        bibliotecario,
        ana,
        libro,
        dias=7,
        fecha_prestamo=date.today() - timedelta(days=20),
    ).json()
    devolver(cliente, bibliotecario, con_retraso["id"])
    cliente.post(
        f"/api/v1/prestamos/{con_retraso['id']}/pago-multa",
        headers=cabecera_staff,
    )

    # Préstamo vencido y aún sin devolver.
    prestar(
        cliente,
        bibliotecario,
        luis,
        libro,
        dias=7,
        fecha_prestamo=date.today() - timedelta(days=20),
    )

    mas_prestados = cliente.get(
        "/api/v1/reportes/libros-mas-prestados",
        headers=cabecera_staff,
    )
    assert mas_prestados.status_code == 200
    assert mas_prestados.json()[0]["total_prestamos"] == 3

    categorias = cliente.get(
        "/api/v1/reportes/categorias", headers=cabecera_staff
    )
    assert categorias.status_code == 200
    assert categorias.json()[0]["total_libros"] == 1

    vencidos = cliente.get(
        "/api/v1/reportes/prestamos-vencidos", headers=cabecera_staff
    )
    assert vencidos.status_code == 200
    assert len(vencidos.json()) == 1
    assert vencidos.json()[0]["dias_retraso"] == 13

    multas = cliente.get(
        "/api/v1/reportes/socios-con-multas", headers=cabecera_staff
    )
    assert multas.status_code == 200
    assert multas.json()[0]["total_multas"] == 6.5

    autores = cliente.get(
        "/api/v1/reportes/autores", headers=cabecera_staff
    )
    assert autores.status_code == 200
    assert autores.json()[0]["total_libros"] == 1

    resumen = cliente.get(
        "/api/v1/reportes/resumen", headers=cabecera_staff
    )
    assert resumen.status_code == 200
    cuerpo = resumen.json()
    assert cuerpo["total_libros"] == 1
    assert cuerpo["total_ejemplares"] == 2
    assert cuerpo["total_prestados"] == 1
    assert cuerpo["total_socios_activos"] == 2
    assert cuerpo["total_socios_vencidos"] == 1
    assert cuerpo["total_multas"] == 6.5
