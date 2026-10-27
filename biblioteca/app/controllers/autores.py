from sqlalchemy.orm import Session
from app.models.autor import Autor
from app.schemas.autor import AutorCreate, AutorUpdate
from app.core.exceptions import Conflicto, NoEncontrado
from typing import Optional


def listar_autores(db: Session, skip: int, limit: int, nacionalidad: Optional[str]):
    q = db.query(Autor)
    if nacionalidad:
        q = q.filter(Autor.nacionalidad.ilike(f"%{nacionalidad}%"))
    return q.offset(skip).limit(limit).all()


def obtener_autor(db: Session, autor_id: int) -> Autor:
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado(f"Autor {autor_id} no encontrado")
    return autor


def crear_autor(db: Session, datos: AutorCreate) -> Autor:
    if db.query(Autor).filter(Autor.nombre == datos.nombre).first():
        raise Conflicto(f"Ya existe un autor con nombre '{datos.nombre}'")
    autor = Autor(**datos.model_dump())
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor


def actualizar_autor(db: Session, autor_id: int, datos: AutorUpdate) -> Autor:
    autor = obtener_autor(db, autor_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != autor.nombre:
        if db.query(Autor).filter(Autor.nombre == cambios["nombre"]).first():
            raise Conflicto(f"Ya existe un autor con nombre '{cambios['nombre']}'")
    for k, v in cambios.items():
        setattr(autor, k, v)
    db.commit()
    db.refresh(autor)
    return autor


def eliminar_autor(db: Session, autor_id: int) -> None:
    autor = obtener_autor(db, autor_id)
    if autor.libros:
        raise Conflicto("No se puede eliminar: el autor tiene libros registrados")
    db.delete(autor)
    db.commit()
