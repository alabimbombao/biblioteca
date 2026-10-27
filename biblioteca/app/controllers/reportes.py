from datetime import date
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from app.models.prestamo import Prestamo
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.socio import Socio
from app.models.categoria import Categoria
from app.models.libro_categoria import libro_categoria


def libros_mas_prestados(db: Session, limite: int = 5):
    """Libro, autor y total de prestamos, de mayor a menor (join + group_by + count + order_by)."""
    rows = (
        db.query(
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
        .all()
    )
    return [
        {
            "libro_id": r.libro_id,
            "titulo": r.titulo,
            "autor": r.autor,
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def categorias_total_libros(db: Session):
    """Total de libros por categoria, incluidas las que tienen 0 (outerjoin + group_by)."""
    total = func.count(libro_categoria.c.libro_id).label("total_libros")
    rows = (
        db.query(Categoria.id.label("categoria_id"), Categoria.nombre, total)
        .outerjoin(libro_categoria, libro_categoria.c.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nombre)
        .all()
    )
    return [
        {"categoria_id": r.categoria_id, "nombre": r.nombre, "total_libros": r.total_libros}
        for r in rows
    ]


def prestamos_vencidos(db: Session):
    """Prestamos vencidos con titulo, socio, email, fecha_limite y dias de retraso
    (join de 3 tablas + where)."""
    hoy = date.today()
    rows = (
        db.query(
            Prestamo.id.label("prestamo_id"),
            Libro.titulo,
            Socio.nombre.label("socio"),
            Socio.email,
            Prestamo.fecha_limite,
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Socio, Prestamo.socio_id == Socio.id)
        .filter(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
        .all()
    )
    return [
        {
            "prestamo_id": r.prestamo_id,
            "titulo": r.titulo,
            "socio": r.socio,
            "email": r.email,
            "fecha_limite": str(r.fecha_limite),
            "dias_retraso": (hoy - r.fecha_limite).days,
        }
        for r in rows
    ]


def socios_con_multas(db: Session):
    """Socio, total de multas y total de prestamos con multa (group_by + sum + having)."""
    rows = (
        db.query(
            Prestamo.socio_id,
            Socio.nombre,
            func.sum(Prestamo.multa).label("total_multas"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Socio, Prestamo.socio_id == Socio.id)
        .filter(Prestamo.multa > 0)
        .group_by(Prestamo.socio_id, Socio.nombre)
        .having(func.sum(Prestamo.multa) > 0)
        .order_by(func.sum(Prestamo.multa).desc())
        .all()
    )
    return [
        {
            "socio_id": r.socio_id,
            "nombre": r.nombre,
            "total_multas": float(r.total_multas),
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def reporte_autores(db: Session):
    """Libros, ejemplares y prestamos de cada autor (outerjoin + count(distinct))."""
    rows = (
        db.query(
            Autor.id.label("autor_id"),
            Autor.nombre,
            func.count(distinct(Libro.id)).label("total_libros"),
            func.coalesce(func.sum(Libro.ejemplares), 0).label("total_ejemplares"),
            func.count(distinct(Prestamo.id)).label("total_prestamos"),
        )
        .outerjoin(Libro, Libro.autor_id == Autor.id)
        .outerjoin(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Autor.id, Autor.nombre)
        .all()
    )
    return [
        {
            "autor_id": r.autor_id,
            "nombre": r.nombre,
            "total_libros": r.total_libros,
            "total_ejemplares": r.total_ejemplares,
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def resumen_biblioteca(db: Session):
    """Totales: libros, ejemplares, prestados, socios activos, vencidos y multas
    (select(func.count()) + func.sum)."""
    hoy = date.today()
    total_libros = db.query(func.count(Libro.id)).scalar()
    total_ejemplares = db.query(func.coalesce(func.sum(Libro.ejemplares), 0)).scalar()
    total_prestados = (
        db.query(func.count(Prestamo.id))
        .filter(Prestamo.fecha_devolucion.is_(None))
        .scalar()
    )
    total_socios_activos = (
        db.query(func.count(Socio.id)).filter(Socio.activo.is_(True)).scalar()
    )
    total_socios_vencidos = (
        db.query(func.count(distinct(Prestamo.socio_id)))
        .filter(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
        .scalar()
    )
    total_multas = db.query(func.coalesce(func.sum(Prestamo.multa), 0)).scalar()
    return {
        "total_libros": total_libros,
        "total_ejemplares": int(total_ejemplares),
        "total_prestados": total_prestados,
        "total_socios_activos": total_socios_activos,
        "total_socios_vencidos": total_socios_vencidos,
        "total_multas": float(total_multas),
    }
