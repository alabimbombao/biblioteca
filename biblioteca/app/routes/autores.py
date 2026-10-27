from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.autor import AutorCreate, AutorUpdate, AutorOut
import app.controllers.autores as ctrl

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get("/", response_model=List[AutorOut])
def listar(pag: PaginacionDep, db: SessionDep, nacionalidad: Optional[str] = None):
    return ctrl.listar_autores(db, pag.skip, pag.limit, nacionalidad)


@router.get("/{autor_id}", response_model=AutorOut)
def obtener(autor_id: int, db: SessionDep):
    return ctrl.obtener_autor(db, autor_id)


@router.post("/", response_model=AutorOut, status_code=201)
def crear(datos: AutorCreate, db: SessionDep):
    return ctrl.crear_autor(db, datos)


@router.patch("/{autor_id}", response_model=AutorOut)
def actualizar(autor_id: int, datos: AutorUpdate, db: SessionDep):
    return ctrl.actualizar_autor(db, autor_id, datos)


@router.delete("/{autor_id}", status_code=204)
def eliminar(autor_id: int, db: SessionDep):
    ctrl.eliminar_autor(db, autor_id)
