"""Controlador de autores."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import Conflicto, NoEncontrado
from app.models.autor import Autor
from app.schemas.autor import AutorCreate, AutorUpdate


def listar_autores(
    db: Session, skip: int, limit: int, nacionalidad: str | None
) -> tuple[list[Autor], int]:
    """Devuelve una página de autores y el total de coincidencias."""
    filtros = []
    if nacionalidad:
        filtros.append(Autor.nacionalidad.ilike(f"%{nacionalidad}%"))

    consulta = select(Autor).where(*filtros)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    items = db.scalars(
        consulta.order_by(Autor.nombre).offset(skip).limit(limit)
    ).all()
    return list(items), total


def obtener_autor(db: Session, autor_id: int) -> Autor:
    """Busca un autor o lanza 404."""
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado(f"Autor {autor_id} no encontrado")
    return autor


def crear_autor(db: Session, datos: AutorCreate) -> Autor:
    """Crea un autor si el nombre no está repetido."""
    existe = db.scalar(select(Autor).where(Autor.nombre == datos.nombre))
    if existe:
        raise Conflicto(f"Ya existe un autor con nombre '{datos.nombre}'")

    autor = Autor(**datos.model_dump())
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor


def actualizar_autor(db: Session, autor_id: int, datos: AutorUpdate) -> Autor:
    """Actualiza los campos enviados de un autor."""
    autor = obtener_autor(db, autor_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "nombre" in cambios and cambios["nombre"] != autor.nombre:
        existe = db.scalar(select(Autor).where(Autor.nombre == cambios["nombre"]))
        if existe:
            raise Conflicto(f"Ya existe un autor con nombre '{cambios['nombre']}'")

    for campo, valor in cambios.items():
        setattr(autor, campo, valor)

    db.commit()
    db.refresh(autor)
    return autor


def eliminar_autor(db: Session, autor_id: int) -> None:
    """Elimina un autor que no tenga libros registrados."""
    autor = obtener_autor(db, autor_id)
    if autor.libros:
        raise Conflicto("No se puede eliminar: el autor tiene libros registrados")

    db.delete(autor)
    db.commit()
