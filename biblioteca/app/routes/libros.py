from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.libro import LibroCreate, LibroUpdate, LibroOut
from app.controllers.libros import OrdenLibro
import app.controllers.libros as ctrl

router = APIRouter(tags=["Libros"])


@router.get("/libros", response_model=List[LibroOut])
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibro] = None,
):
    return ctrl.listar_libros(
        db, pag.skip, pag.limit, buscar, autor, categoria_id, desde, hasta, orden
    )


@router.get("/libros/{libro_id}", response_model=LibroOut)
def obtener(libro_id: int, db: SessionDep):
    return ctrl.obtener_libro(db, libro_id)


@router.post("/libros", response_model=LibroOut, status_code=201)
def crear(datos: LibroCreate, db: SessionDep):
    return ctrl.crear_libro(db, datos)


@router.patch("/libros/{libro_id}", response_model=LibroOut)
def actualizar(libro_id: int, datos: LibroUpdate, db: SessionDep):
    return ctrl.actualizar_libro(db, libro_id, datos)


@router.delete("/libros/{libro_id}", status_code=204)
def eliminar(libro_id: int, db: SessionDep):
    ctrl.eliminar_libro(db, libro_id)


@router.get("/autores/{autor_id}/libros", response_model=List[LibroOut], tags=["Autores"])
def libros_de_autor(autor_id: int, pag: PaginacionDep, db: SessionDep):
    return ctrl.libros_de_autor(db, autor_id, pag.skip, pag.limit)
