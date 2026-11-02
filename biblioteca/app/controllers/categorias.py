"""Controlador de categorías."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import Conflicto, NoEncontrado
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def listar_categorias(
    db: Session, skip: int, limit: int
) -> tuple[list[Categoria], int]:
    """Devuelve una página de categorías y el total."""
    consulta = select(Categoria)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    items = db.scalars(
        consulta.order_by(Categoria.nombre).offset(skip).limit(limit)
    ).all()
    return list(items), total


def obtener_categoria(db: Session, categoria_id: int) -> Categoria:
    """Busca una categoría o lanza 404."""
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise NoEncontrado(f"Categoria {categoria_id} no encontrada")
    return categoria


def crear_categoria(db: Session, datos: CategoriaCreate) -> Categoria:
    """Crea una categoría si el nombre no está repetido."""
    existe = db.scalar(
        select(Categoria).where(Categoria.nombre == datos.nombre)
    )
    if existe:
        raise Conflicto(f"Ya existe la categoria '{datos.nombre}'")

    categoria = Categoria(**datos.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def actualizar_categoria(
    db: Session, categoria_id: int, datos: CategoriaUpdate
) -> Categoria:
    """Actualiza los campos enviados de una categoría."""
    categoria = obtener_categoria(db, categoria_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "nombre" in cambios and cambios["nombre"] != categoria.nombre:
        existe = db.scalar(
            select(Categoria).where(Categoria.nombre == cambios["nombre"])
        )
        if existe:
            raise Conflicto(f"Ya existe la categoria '{cambios['nombre']}'")

    for campo, valor in cambios.items():
        setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar_categoria(db: Session, categoria_id: int) -> None:
    """Elimina una categoría y la desvincula de sus libros."""
    categoria = obtener_categoria(db, categoria_id)
    categoria.libros.clear()
    db.delete(categoria)
    db.commit()
