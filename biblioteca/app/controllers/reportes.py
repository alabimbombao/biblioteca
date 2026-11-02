"""Controlador de reportes del Taller 1."""

from datetime import date

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.libro import Libro
from app.models.libro_categoria import libro_categoria
from app.models.prestamo import Prestamo
from app.models.socio import Socio


def libros_mas_prestados(db: Session, limite: int = 5) -> list[dict]:
    """Libros ordenados por cantidad de préstamos."""
    consulta = (
        select(
            Prestamo.libro_id,
            Libro.titulo,
            Autor.nombre.label("autor"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Autor, Libro.autor_id == Autor.id)
        .group_by(Prestamo.libro_id, Libro.titulo, Autor.nombre)
        .order_by(func.count(Prestamo.id).desc())
        .limit(limite)
    )
    filas = db.execute(consulta).all()
    return [
        {
            "libro_id": fila.libro_id,
            "titulo": fila.titulo,
            "autor": fila.autor,
            "total_prestamos": fila.total_prestamos,
        }
        for fila in filas
    ]


def categorias_total_libros(db: Session) -> list[dict]:
    """Total de libros por categoría, incluidas las que tienen cero."""
    total = func.count(libro_categoria.c.libro_id).label("total_libros")
    consulta = (
        select(Categoria.id.label("categoria_id"), Categoria.nombre, total)
        .outerjoin(
            libro_categoria,
            libro_categoria.c.categoria_id == Categoria.id,
        )
        .group_by(Categoria.id, Categoria.nombre)
        .order_by(Categoria.nombre)
    )
    filas = db.execute(consulta).all()
    return [
        {
            "categoria_id": fila.categoria_id,
            "nombre": fila.nombre,
            "total_libros": fila.total_libros,
        }
        for fila in filas
    ]


def prestamos_vencidos(db: Session) -> list[dict]:
    """Préstamos vencidos con sus días de retraso."""
    hoy = date.today()
    consulta = (
        select(
            Prestamo.id.label("prestamo_id"),
            Libro.titulo,
            Socio.nombre.label("socio"),
            Socio.email,
            Prestamo.fecha_limite,
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Socio, Prestamo.socio_id == Socio.id)
        .where(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
        .order_by(Prestamo.fecha_limite)
    )
    filas = db.execute(consulta).all()
    return [
        {
            "prestamo_id": fila.prestamo_id,
            "titulo": fila.titulo,
            "socio": fila.socio,
            "email": fila.email,
            "fecha_limite": str(fila.fecha_limite),
            "dias_retraso": (hoy - fila.fecha_limite).days,
        }
        for fila in filas
    ]


def socios_con_multas(db: Session) -> list[dict]:
    """Socios con multas acumuladas, de mayor a menor."""
    consulta = (
        select(
            Prestamo.socio_id,
            Socio.nombre,
            func.sum(Prestamo.multa).label("total_multas"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Socio, Prestamo.socio_id == Socio.id)
        .where(Prestamo.multa > 0)
        .group_by(Prestamo.socio_id, Socio.nombre)
        .having(func.sum(Prestamo.multa) > 0)
        .order_by(func.sum(Prestamo.multa).desc())
    )
    filas = db.execute(consulta).all()
    return [
        {
            "socio_id": fila.socio_id,
            "nombre": fila.nombre,
            "total_multas": float(fila.total_multas),
            "total_prestamos": fila.total_prestamos,
        }
        for fila in filas
    ]


def reporte_autores(db: Session) -> list[dict]:
    """Libros, ejemplares y préstamos de cada autor."""
    consulta = (
        select(
            Autor.id.label("autor_id"),
            Autor.nombre,
            func.count(distinct(Libro.id)).label("total_libros"),
            func.coalesce(func.sum(Libro.ejemplares), 0).label("total_ejemplares"),
            func.count(distinct(Prestamo.id)).label("total_prestamos"),
        )
        .outerjoin(Libro, Libro.autor_id == Autor.id)
        .outerjoin(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Autor.id, Autor.nombre)
        .order_by(Autor.nombre)
    )
    filas = db.execute(consulta).all()
    return [
        {
            "autor_id": fila.autor_id,
            "nombre": fila.nombre,
            "total_libros": fila.total_libros,
            "total_ejemplares": fila.total_ejemplares,
            "total_prestamos": fila.total_prestamos,
        }
        for fila in filas
    ]


def resumen_biblioteca(db: Session) -> dict:
    """Totales generales de la biblioteca."""
    hoy = date.today()
    total_libros = db.scalar(select(func.count(Libro.id))) or 0
    total_ejemplares = db.scalar(
        select(func.coalesce(func.sum(Libro.ejemplares), 0))
    ) or 0
    total_prestados = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.fecha_devolucion.is_(None)
        )
    ) or 0
    total_socios_activos = db.scalar(
        select(func.count(Socio.id)).where(Socio.activo.is_(True))
    ) or 0
    total_socios_vencidos = db.scalar(
        select(func.count(distinct(Prestamo.socio_id))).where(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
    ) or 0
    total_multas = db.scalar(
        select(func.coalesce(func.sum(Prestamo.multa), 0))
    ) or 0

    return {
        "total_libros": total_libros,
        "total_ejemplares": int(total_ejemplares),
        "total_prestados": total_prestados,
        "total_socios_activos": total_socios_activos,
        "total_socios_vencidos": total_socios_vencidos,
        "total_multas": float(total_multas),
    }
