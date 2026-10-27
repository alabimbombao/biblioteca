from sqlalchemy.orm import Session
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.core.exceptions import Conflicto, NoEncontrado


def listar_categorias(db: Session, skip: int, limit: int):
    return db.query(Categoria).offset(skip).limit(limit).all()


def obtener_categoria(db: Session, categoria_id: int) -> Categoria:
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise NoEncontrado(f"Categoria {categoria_id} no encontrada")
    return cat


def crear_categoria(db: Session, datos: CategoriaCreate) -> Categoria:
    if db.query(Categoria).filter(Categoria.nombre == datos.nombre).first():
        raise Conflicto(f"Ya existe la categoria '{datos.nombre}'")
    cat = Categoria(**datos.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def actualizar_categoria(db: Session, categoria_id: int, datos: CategoriaUpdate) -> Categoria:
    cat = obtener_categoria(db, categoria_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != cat.nombre:
        if db.query(Categoria).filter(Categoria.nombre == cambios["nombre"]).first():
            raise Conflicto(f"Ya existe la categoria '{cambios['nombre']}'")
    for k, v in cambios.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def eliminar_categoria(db: Session, categoria_id: int) -> None:
    cat = obtener_categoria(db, categoria_id)
    # Quitar de todos los libros (relacion M:N)
    cat.libros.clear()
    db.delete(cat)
    db.commit()
