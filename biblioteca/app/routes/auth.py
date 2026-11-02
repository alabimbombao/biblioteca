"""Rutas de autenticación."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.controllers import auth as ctrl
from app.core.dependencies import CurrentUser, SessionDep
from app.core.rate_limit import limiter
from app.routes.respuestas import RESPUESTAS_AUTENTICADO
from app.schemas.auth import (
    CambioPassword,
    RefreshSolicitud,
    TokenRespuesta,
    UsuarioRegistro,
    UsuarioRespuesta,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=201,
    summary="Registrar un socio",
    responses={409: {"description": "El email ya existe"}},
)
@limiter.limit("5/minute")
def registrar(
    request: Request,
    datos: UsuarioRegistro,
    db: SessionDep,
):
    """Registro público. Crea el usuario socio y su socio vinculado."""
    return ctrl.registrar(db, datos)


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Iniciar sesión",
    responses={
        401: {"description": "Credenciales inválidas"},
        423: {"description": "Cuenta bloqueada temporalmente"},
        429: {"description": "Demasiadas peticiones"},
    },
)
@limiter.limit("10/minute")
def iniciar_sesion(
    request: Request,
    db: SessionDep,
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Login con el flujo OAuth2 Password (username = email)."""
    return ctrl.iniciar_sesion(db, formulario.username, formulario.password)


@router.post(
    "/refresh",
    response_model=TokenRespuesta,
    summary="Renovar el par de tokens",
    responses={401: {"description": "Refresh token inválido o vencido"}},
)
def refrescar(datos: RefreshSolicitud, db: SessionDep):
    """Rota el refresh token y entrega un par nuevo."""
    return ctrl.refrescar(db, datos.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Cerrar sesión",
    responses=RESPUESTAS_AUTENTICADO,
)
def cerrar_sesion(
    datos: RefreshSolicitud,
    db: SessionDep,
    _usuario: CurrentUser,
):
    """Revoca el refresh token entregado por el cliente."""
    ctrl.cerrar_sesion(db, datos.refresh_token)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Datos del usuario autenticado",
    responses=RESPUESTAS_AUTENTICADO,
)
def yo(usuario: CurrentUser):
    """Devuelve los datos del usuario autenticado."""
    return usuario


@router.patch(
    "/me/password",
    status_code=204,
    summary="Cambiar la contraseña",
    responses=RESPUESTAS_AUTENTICADO,
)
def cambiar_password(
    datos: CambioPassword,
    db: SessionDep,
    usuario: CurrentUser,
):
    """Cambia la contraseña y revoca todos los refresh tokens."""
    ctrl.cambiar_password(db, usuario, datos)
