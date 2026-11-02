"""Rutas de autores."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.controllers import autores as ctrl
from app.core.dependencies import PaginacionDep, SessionDep, SoloAdmin, Staff
from app.routes.respuestas import RESPUESTAS_ADMIN, RESPUESTAS_PUBLICAS, RESPUESTAS_STAFF
from app.schemas.autor import AutorCreate, AutorOut, AutorUpdate
from app.schemas.pagina import Pagina

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get(
    "",
    response_model=Pagina[AutorOut],
    summary="Listar autores",
    responses=RESPUESTAS_PUBLICAS,
)
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    nacionalidad: Annotated[
        str | None, Query(description="Filtro por nacionalidad")
    ] = None,
):
    """Lista pública de autores con paginación."""
    items, total = ctrl.listar_autores(db, pag.skip, pag.limit, nacionalidad)
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.get(
    "/{autor_id}",
    response_model=AutorOut,
    summary="Obtener un autor",
    responses=RESPUESTAS_PUBLICAS,
)
def obtener(autor_id: int, db: SessionDep):
    """Devuelve un autor por su identificador."""
    return ctrl.obtener_autor(db, autor_id)


@router.post(
    "",
    response_model=AutorOut,
    status_code=201,
    summary="Crear un autor",
    responses=RESPUESTAS_STAFF,
)
def crear(datos: AutorCreate, db: SessionDep, _usuario: Staff):
    """Crea un autor. Requiere rol bibliotecario o admin."""
    return ctrl.crear_autor(db, datos)


@router.patch(
    "/{autor_id}",
    response_model=AutorOut,
    summary="Actualizar un autor",
    responses=RESPUESTAS_STAFF,
)
def actualizar(
    autor_id: int, datos: AutorUpdate, db: SessionDep, _usuario: Staff
):
    """Actualiza un autor. Requiere rol bibliotecario o admin."""
    return ctrl.actualizar_autor(db, autor_id, datos)


@router.delete(
    "/{autor_id}",
    status_code=204,
    summary="Eliminar un autor",
    responses=RESPUESTAS_ADMIN,
)
def eliminar(autor_id: int, db: SessionDep, _usuario: SoloAdmin):
    """Elimina un autor. Solo el administrador puede hacerlo."""
    ctrl.eliminar_autor(db, autor_id)
