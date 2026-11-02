"""Rutas de socios, incluidos los endpoints del propio socio."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.controllers import socios as ctrl
from app.core.dependencies import (
    PaginacionDep,
    SessionDep,
    SoloAdmin,
    SoloSocio,
    Staff,
)
from app.routes.respuestas import (
    RESPUESTAS_ADMIN,
    RESPUESTAS_AUTENTICADO,
    RESPUESTAS_STAFF,
)
from app.schemas.pagina import Pagina
from app.schemas.prestamo import MultasSocio, PrestamoOut
from app.schemas.socio import (
    SocioActualizarPropio,
    SocioCreate,
    SocioOut,
    SocioUpdate,
)

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.get(
    "/me",
    response_model=SocioOut,
    summary="Perfil del socio autenticado",
    responses=RESPUESTAS_AUTENTICADO,
)
def mi_perfil(db: SessionDep, usuario: SoloSocio):
    """Devuelve el perfil del socio vinculado al usuario autenticado."""
    return ctrl.socio_del_usuario(usuario)


@router.patch(
    "/me",
    response_model=SocioOut,
    summary="Editar el perfil propio",
    responses=RESPUESTAS_AUTENTICADO,
)
def actualizar_mi_perfil(
    datos: SocioActualizarPropio,
    db: SessionDep,
    usuario: SoloSocio,
):
    """Un socio solo puede cambiar su nombre y su teléfono."""
    return ctrl.actualizar_perfil_propio(db, usuario, datos)


@router.get(
    "/me/prestamos",
    response_model=Pagina[PrestamoOut],
    summary="Préstamos del socio autenticado",
    responses=RESPUESTAS_AUTENTICADO,
)
def mis_prestamos(
    pag: PaginacionDep,
    db: SessionDep,
    usuario: SoloSocio,
    estado: Annotated[
        str | None,
        Query(description="Filtro: activo, vencido o devuelto"),
    ] = None,
):
    """Lista los préstamos propios, con filtro por estado."""
    items, total = ctrl.prestamos_propios(
        db, usuario, pag.skip, pag.limit, estado
    )
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.get(
    "/me/multas",
    response_model=MultasSocio,
    summary="Multas sin pagar del socio autenticado",
    responses=RESPUESTAS_AUTENTICADO,
)
def mis_multas(db: SessionDep, usuario: SoloSocio):
    """Devuelve las multas pendientes y el total adeudado."""
    items, total_adeudado = ctrl.multas_propias(db, usuario)
    return {"items": items, "total_adeudado": total_adeudado}


@router.get(
    "",
    response_model=Pagina[SocioOut],
    summary="Listar socios",
    responses=RESPUESTAS_STAFF,
)
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    _usuario: Staff,
    activo: Annotated[
        bool | None, Query(description="Filtro por estado activo")
    ] = None,
):
    """Lista socios. Requiere rol bibliotecario o admin."""
    items, total = ctrl.listar_socios(db, pag.skip, pag.limit, activo)
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.post(
    "",
    response_model=SocioOut,
    status_code=201,
    summary="Crear un socio",
    responses=RESPUESTAS_STAFF,
)
def crear(datos: SocioCreate, db: SessionDep, _usuario: Staff):
    """Crea un socio. Requiere rol bibliotecario o admin."""
    return ctrl.crear_socio(db, datos)


@router.get(
    "/{socio_id}",
    response_model=SocioOut,
    summary="Obtener un socio",
    responses=RESPUESTAS_STAFF,
)
def obtener(socio_id: int, db: SessionDep, _usuario: Staff):
    """Devuelve un socio por su identificador."""
    return ctrl.obtener_socio(db, socio_id)


@router.patch(
    "/{socio_id}",
    response_model=SocioOut,
    summary="Actualizar un socio",
    responses=RESPUESTAS_STAFF,
)
def actualizar(
    socio_id: int, datos: SocioUpdate, db: SessionDep, _usuario: Staff
):
    """Actualiza un socio. Requiere rol bibliotecario o admin."""
    return ctrl.actualizar_socio(db, socio_id, datos)


@router.delete(
    "/{socio_id}",
    status_code=204,
    summary="Eliminar un socio",
    responses=RESPUESTAS_ADMIN,
)
def eliminar(socio_id: int, db: SessionDep, _usuario: SoloAdmin):
    """Elimina o desactiva un socio. Solo el administrador puede hacerlo."""
    ctrl.eliminar_socio(db, socio_id)


@router.get(
    "/{socio_id}/prestamos",
    response_model=Pagina[PrestamoOut],
    summary="Préstamos de un socio",
    responses=RESPUESTAS_STAFF,
)
def prestamos_del_socio(
    socio_id: int,
    pag: PaginacionDep,
    db: SessionDep,
    _usuario: Staff,
    estado: Annotated[
        str | None,
        Query(description="Filtro: activo, vencido o devuelto"),
    ] = None,
):
    """Lista los préstamos de un socio. Requiere staff."""
    items, total = ctrl.prestamos_de_socio(
        db, socio_id, pag.skip, pag.limit, estado
    )
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }
