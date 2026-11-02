"""Rutas de categorías."""

from fastapi import APIRouter

from app.controllers import categorias as ctrl
from app.core.dependencies import PaginacionDep, SessionDep, SoloAdmin, Staff
from app.routes.respuestas import RESPUESTAS_ADMIN, RESPUESTAS_PUBLICAS, RESPUESTAS_STAFF
from app.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate
from app.schemas.pagina import Pagina

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get(
    "",
    response_model=Pagina[CategoriaOut],
    summary="Listar categorías",
    responses=RESPUESTAS_PUBLICAS,
)
def listar(pag: PaginacionDep, db: SessionDep):
    """Lista pública de categorías con paginación."""
    items, total = ctrl.listar_categorias(db, pag.skip, pag.limit)
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.post(
    "",
    response_model=CategoriaOut,
    status_code=201,
    summary="Crear una categoría",
    responses=RESPUESTAS_STAFF,
)
def crear(datos: CategoriaCreate, db: SessionDep, _usuario: Staff):
    """Crea una categoría. Requiere rol bibliotecario o admin."""
    return ctrl.crear_categoria(db, datos)


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaOut,
    summary="Actualizar una categoría",
    responses=RESPUESTAS_STAFF,
)
def actualizar(
    categoria_id: int,
    datos: CategoriaUpdate,
    db: SessionDep,
    _usuario: Staff,
):
    """Actualiza una categoría. Requiere rol bibliotecario o admin."""
    return ctrl.actualizar_categoria(db, categoria_id, datos)


@router.delete(
    "/{categoria_id}",
    status_code=204,
    summary="Eliminar una categoría",
    responses=RESPUESTAS_ADMIN,
)
def eliminar(categoria_id: int, db: SessionDep, _usuario: SoloAdmin):
    """Elimina una categoría. Solo el administrador puede hacerlo."""
    ctrl.eliminar_categoria(db, categoria_id)
