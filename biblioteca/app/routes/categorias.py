from fastapi import APIRouter
from typing import List
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaOut
import app.controllers.categorias as ctrl

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/", response_model=List[CategoriaOut])
def listar(pag: PaginacionDep, db: SessionDep):
    return ctrl.listar_categorias(db, pag.skip, pag.limit)


@router.post("/", response_model=CategoriaOut, status_code=201)
def crear(datos: CategoriaCreate, db: SessionDep):
    return ctrl.crear_categoria(db, datos)


@router.patch("/{categoria_id}", response_model=CategoriaOut)
def actualizar(categoria_id: int, datos: CategoriaUpdate, db: SessionDep):
    return ctrl.actualizar_categoria(db, categoria_id, datos)


@router.delete("/{categoria_id}", status_code=204)
def eliminar(categoria_id: int, db: SessionDep):
    ctrl.eliminar_categoria(db, categoria_id)
