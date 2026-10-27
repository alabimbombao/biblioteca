from enum import Enum
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.prestamo import Prestamo
from app.schemas.libro import LibroCreate, LibroUpdate
from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from typing import Optional


class OrdenLibro(str, Enum):
    titulo = "titulo"
    anio = "anio"


def _activos_libro(db: Session, libro_id: int) -> int:
    return (
        db.query(func.count(Prestamo.id))
        .filter(Prestamo.libro_id == libro_id, Prestamo.fecha_devolucion.is_(None))
        .scalar()
    )


def _enriquecer(libro: Libro, db: Session) -> Libro:
    libro.disponibles = libro.ejemplares - _activos_libro(db, libro.id)
    return libro


def listar_libros(
    db: Session,
    skip: int,
    limit: int,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibro] = None,
):
    q = db.query(Libro).options(selectinload(Libro.autor), selectinload(Libro.categorias))
    if buscar:
        q = q.filter(Libro.titulo.ilike(f"%{buscar}%"))
    if autor:
        q = q.join(Libro.autor).filter(Autor.nombre.ilike(f"%{autor}%"))
    if categoria_id:
        q = q.join(Libro.categorias).filter(Categoria.id == categoria_id)
    if desde:
        q = q.filter(Libro.anio_publicacion >= desde)
    if hasta:
        q = q.filter(Libro.anio_publicacion <= hasta)
    if orden == OrdenLibro.anio:
        q = q.order_by(Libro.anio_publicacion.desc())
    else:
        q = q.order_by(Libro.titulo)
    libros = q.offset(skip).limit(limit).all()
    for l in libros:
        _enriquecer(l, db)
    return libros


def obtener_libro(db: Session, libro_id: int) -> Libro:
    libro = (
        db.query(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .filter(Libro.id == libro_id)
        .first()
    )
    if not libro:
        raise NoEncontrado(f"Libro {libro_id} no encontrado")
    return _enriquecer(libro, db)


def crear_libro(db: Session, datos: LibroCreate) -> Libro:
    if not db.get(Autor, datos.autor_id):
        raise NoEncontrado(f"Autor {datos.autor_id} no encontrado")
    if db.query(Libro).filter(Libro.isbn == datos.isbn).first():
        raise Conflicto(f"Ya existe un libro con ISBN '{datos.isbn}'")
    categorias = []
    for cid in datos.categoria_ids:
        cat = db.get(Categoria, cid)
        if not cat:
            raise NoEncontrado(f"Categoria {cid} no encontrada")
        categorias.append(cat)
    libro_data = datos.model_dump(exclude={"categoria_ids"})
    libro = Libro(**libro_data)
    libro.categorias = categorias
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return obtener_libro(db, libro.id)


def actualizar_libro(db: Session, libro_id: int, datos: LibroUpdate) -> Libro:
    libro = obtener_libro(db, libro_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "categoria_ids" in cambios:
        categorias = []
        for cid in cambios.pop("categoria_ids"):
            cat = db.get(Categoria, cid)
            if not cat:
                raise NoEncontrado(f"Categoria {cid} no encontrada")
            categorias.append(cat)
        libro.categorias = categorias
    if "ejemplares" in cambios:
        activos = _activos_libro(db, libro_id)
        if cambios["ejemplares"] < activos:
            raise ReglaNegocio(
                f"No se puede reducir ejemplares: hay {activos} prestamos activos"
            )
    for k, v in cambios.items():
        setattr(libro, k, v)
    db.commit()
    return obtener_libro(db, libro_id)


def eliminar_libro(db: Session, libro_id: int) -> None:
    libro = obtener_libro(db, libro_id)
    activos = _activos_libro(db, libro_id)
    if activos:
        raise Conflicto("No se puede eliminar: el libro tiene prestamos sin devolver")
    db.delete(libro)
    db.commit()


def libros_de_autor(db: Session, autor_id: int, skip: int, limit: int):
    if not db.get(Autor, autor_id):
        raise NoEncontrado(f"Autor {autor_id} no encontrado")
    libros = (
        db.query(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .filter(Libro.autor_id == autor_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    for l in libros:
        _enriquecer(l, db)
    return libros
