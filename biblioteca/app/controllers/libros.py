"""Controlador de libros."""

from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.libro import Libro
from app.models.prestamo import Prestamo
from app.schemas.libro import LibroCreate, LibroUpdate


class OrdenLibro(str, Enum):
    """Criterios de ordenamiento del catálogo."""

    titulo = "titulo"
    anio = "anio"


def _activos_libro(db: Session, libro_id: int) -> int:
    """Cuenta los préstamos sin devolver de un libro."""
    return db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0


def _enriquecer(libro: Libro, db: Session) -> Libro:
    """Calcula los ejemplares disponibles del libro."""
    libro.disponibles = libro.ejemplares - _activos_libro(db, libro.id)
    return libro


def listar_libros(
    db: Session,
    skip: int,
    limit: int,
    buscar: str | None = None,
    autor: str | None = None,
    categoria_id: int | None = None,
    desde: int | None = None,
    hasta: int | None = None,
    orden: OrdenLibro | None = None,
) -> tuple[list[Libro], int]:
    """Lista libros con búsqueda, filtros y paginación."""
    consulta = select(Libro).options(
        selectinload(Libro.autor),
        selectinload(Libro.categorias),
    )
    filtros = []

    if buscar:
        filtros.append(Libro.titulo.ilike(f"%{buscar}%"))
    if autor:
        consulta = consulta.join(Libro.autor)
        filtros.append(Autor.nombre.ilike(f"%{autor}%"))
    if categoria_id:
        consulta = consulta.join(Libro.categorias)
        filtros.append(Categoria.id == categoria_id)
    if desde:
        filtros.append(Libro.anio_publicacion >= desde)
    if hasta:
        filtros.append(Libro.anio_publicacion <= hasta)

    consulta = consulta.where(*filtros)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0

    if orden == OrdenLibro.anio:
        consulta = consulta.order_by(Libro.anio_publicacion.desc())
    else:
        consulta = consulta.order_by(Libro.titulo)

    libros = db.scalars(consulta.offset(skip).limit(limit)).all()
    for libro in libros:
        _enriquecer(libro, db)

    return list(libros), total


def obtener_libro(db: Session, libro_id: int) -> Libro:
    """Busca un libro con sus relaciones o lanza 404."""
    libro = db.scalar(
        select(Libro)
        .options(
            selectinload(Libro.autor),
            selectinload(Libro.categorias),
        )
        .where(Libro.id == libro_id)
    )
    if not libro:
        raise NoEncontrado(f"Libro {libro_id} no encontrado")
    return _enriquecer(libro, db)


def crear_libro(db: Session, datos: LibroCreate) -> Libro:
    """Crea un libro validando autor, ISBN y categorías."""
    if not db.get(Autor, datos.autor_id):
        raise NoEncontrado(f"Autor {datos.autor_id} no encontrado")
    if db.scalar(select(Libro).where(Libro.isbn == datos.isbn)):
        raise Conflicto(f"Ya existe un libro con ISBN '{datos.isbn}'")

    categorias = []
    for categoria_id in datos.categoria_ids:
        categoria = db.get(Categoria, categoria_id)
        if not categoria:
            raise NoEncontrado(f"Categoria {categoria_id} no encontrada")
        categorias.append(categoria)

    datos_libro = datos.model_dump(exclude={"categoria_ids"})
    libro = Libro(**datos_libro)
    libro.categorias = categorias

    db.add(libro)
    db.commit()
    db.refresh(libro)
    return obtener_libro(db, libro.id)


def actualizar_libro(
    db: Session, libro_id: int, datos: LibroUpdate
) -> Libro:
    """Actualiza un libro respetando los ejemplares prestados."""
    libro = obtener_libro(db, libro_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "categoria_ids" in cambios:
        categorias = []
        for categoria_id in cambios.pop("categoria_ids"):
            categoria = db.get(Categoria, categoria_id)
            if not categoria:
                raise NoEncontrado(f"Categoria {categoria_id} no encontrada")
            categorias.append(categoria)
        libro.categorias = categorias

    if "ejemplares" in cambios:
        activos = _activos_libro(db, libro_id)
        if cambios["ejemplares"] < activos:
            raise ReglaNegocio(
                f"No se puede reducir ejemplares: hay {activos} prestamos activos"
            )

    for campo, valor in cambios.items():
        setattr(libro, campo, valor)

    db.commit()
    return obtener_libro(db, libro_id)


def eliminar_libro(db: Session, libro_id: int) -> None:
    """Elimina un libro sin préstamos pendientes."""
    libro = obtener_libro(db, libro_id)
    if _activos_libro(db, libro_id):
        raise Conflicto("No se puede eliminar: el libro tiene prestamos sin devolver")

    db.delete(libro)
    db.commit()


def libros_de_autor(
    db: Session, autor_id: int, skip: int, limit: int
) -> tuple[list[Libro], int]:
    """Lista los libros de un autor."""
    if not db.get(Autor, autor_id):
        raise NoEncontrado(f"Autor {autor_id} no encontrado")

    consulta = select(Libro).where(Libro.autor_id == autor_id)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    libros = db.scalars(
        consulta.options(
            selectinload(Libro.autor),
            selectinload(Libro.categorias),
        )
        .order_by(Libro.titulo)
        .offset(skip)
        .limit(limit)
    ).all()

    for libro in libros:
        _enriquecer(libro, db)

    return list(libros), total
