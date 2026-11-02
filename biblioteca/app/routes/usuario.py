"""Rutas de administración de usuarios (solo admin)."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.controllers import usuario as ctrl
from app.core.dependencies import PaginacionDep, SessionDep, SoloAdmin
from app.models.usuario import RolUsuario
from app.routes.respuestas import RESPUESTAS_ADMIN
from app.schemas.pagina import Pagina
from app.schemas.usuario import (
    ActivoActualizar,
    RolActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get(
    "",
    response_model=Pagina[UsuarioRespuesta],
    summary="Listar usuarios",
    responses=RESPUESTAS_ADMIN,
)
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    _admin: SoloAdmin,
    rol: Annotated[
        RolUsuario | None, Query(description="Filtro por rol")
    ] = None,
    activo: Annotated[
        bool | None, Query(description="Filtro por estado activo")
    ] = None,
):
    """Lista usuarios con filtros por rol y estado."""
    items, total = ctrl.listar_usuarios(
        db, pag.skip, pag.limit, rol, activo
    )
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=201,
    summary="Crear un usuario del staff",
    responses=RESPUESTAS_ADMIN,
)
def crear(datos: UsuarioCrear, db: SessionDep, _admin: SoloAdmin):
    """Crea un usuario bibliotecario o admin."""
    return ctrl.crear_usuario(db, datos)


@router.patch(
    "/{usuario_id}/rol",
    response_model=UsuarioRespuesta,
    summary="Cambiar el rol de un usuario",
    responses=RESPUESTAS_ADMIN,
)
def cambiar_rol(
    usuario_id: int,
    datos: RolActualizar,
    db: SessionDep,
    actual: SoloAdmin,
):
    """Cambia el rol y revoca los refresh tokens del usuario."""
    return ctrl.cambiar_rol(db, usuario_id, datos, actual)


@router.patch(
    "/{usuario_id}/activo",
    response_model=UsuarioRespuesta,
    summary="Activar o desactivar un usuario",
    responses=RESPUESTAS_ADMIN,
)
def cambiar_activo(
    usuario_id: int,
    datos: ActivoActualizar,
    db: SessionDep,
    actual: SoloAdmin,
):
    """Activa o desactiva un usuario y revoca sus tokens si se desactiva."""
    return ctrl.cambiar_activo(db, usuario_id, datos, actual)
