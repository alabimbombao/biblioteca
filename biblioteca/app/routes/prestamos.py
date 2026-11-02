"""Rutas de préstamos y pago de multas."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.controllers import prestamos as ctrl
from app.core.dependencies import CurrentUser, PaginacionDep, SessionDep, Staff
from app.routes.respuestas import RESPUESTAS_AUTENTICADO, RESPUESTAS_STAFF
from app.schemas.pagina import Pagina
from app.schemas.prestamo import (
    PrestamoCreate,
    PrestamoDevolucion,
    PrestamoOut,
)

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.get(
    "",
    response_model=Pagina[PrestamoOut],
    summary="Listar préstamos",
    responses=RESPUESTAS_AUTENTICADO,
)
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    usuario: CurrentUser,
    estado: Annotated[
        str | None,
        Query(description="Filtro: activo, vencido o devuelto"),
    ] = None,
    socio_id: Annotated[
        int | None, Query(description="Filtro por socio (solo staff)")
    ] = None,
    libro_id: Annotated[
        int | None, Query(description="Filtro por libro")
    ] = None,
):
    """Lista préstamos. Un socio solo ve los suyos."""
    items, total = ctrl.listar_prestamos(
        db,
        usuario,
        pag.skip,
        pag.limit,
        estado,
        socio_id,
        libro_id,
    )
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.get(
    "/{prestamo_id}",
    response_model=PrestamoOut,
    summary="Obtener un préstamo",
    responses=RESPUESTAS_AUTENTICADO,
)
def obtener(prestamo_id: int, db: SessionDep, usuario: CurrentUser):
    """Devuelve un préstamo propio o, para staff, cualquiera."""
    return ctrl.obtener_prestamo(db, prestamo_id, usuario)


@router.post(
    "",
    response_model=PrestamoOut,
    status_code=201,
    summary="Registrar un préstamo",
    responses=RESPUESTAS_STAFF,
)
def crear(datos: PrestamoCreate, db: SessionDep, usuario: Staff):
    """Registra un préstamo y guarda quién lo registró (Z7)."""
    return ctrl.crear_prestamo(db, datos, usuario)


@router.post(
    "/{prestamo_id}/devolucion",
    response_model=PrestamoOut,
    summary="Registrar una devolución",
    responses=RESPUESTAS_STAFF,
)
def devolver(
    prestamo_id: int,
    datos: PrestamoDevolucion,
    db: SessionDep,
    _usuario: Staff,
):
    """Registra la devolución y calcula la multa si hay retraso."""
    return ctrl.devolver_prestamo(db, prestamo_id, datos)


@router.post(
    "/{prestamo_id}/pago-multa",
    response_model=PrestamoOut,
    summary="Pagar la multa de un préstamo",
    responses=RESPUESTAS_STAFF,
)
def pagar_multa(prestamo_id: int, db: SessionDep, _usuario: Staff):
    """Marca la multa como pagada. Responde 409 si no hay multa pendiente."""
    return ctrl.pagar_multa(db, prestamo_id)
