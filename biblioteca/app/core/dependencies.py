"""Dependencias reutilizables de FastAPI."""

from typing import Annotated, Generator

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import NoAutenticado, Prohibido
from app.core.security import decodificar_token
from app.models.usuario import RolUsuario, Usuario

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: SessionDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Usuario:
    """Obtiene el usuario autenticado a partir del access token."""
    if not token:
        raise NoAutenticado("No autenticado")

    payload = decodificar_token(token, "access")

    try:
        usuario_id = int(payload.get("sub", ""))
    except (TypeError, ValueError) as exc:
        raise NoAutenticado("Token inválido o vencido") from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise NoAutenticado("Token inválido o vencido")

    # El usuario se consulta en cada petición: si fue desactivado,
    # su token deja de servir (regla A7).
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def requiere_rol(*roles: RolUsuario):
    """Dependencia reutilizable de autorización por rol."""

    def verificar(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise Prohibido("No tiene permisos para esta acción")
        return usuario

    return Depends(verificar)


Staff = Annotated[Usuario, requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)]
SoloAdmin = Annotated[Usuario, requiere_rol(RolUsuario.admin)]
SoloSocio = Annotated[Usuario, requiere_rol(RolUsuario.socio)]


class Paginacion:
    """Parámetros de paginación comunes a todos los listados."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Registros a omitir"),
        limit: int = Query(default=10, ge=1, le=100, description="Máximo de registros"),
    ):
        self.skip = skip
        self.limit = limit


PaginacionDep = Annotated[Paginacion, Depends()]
