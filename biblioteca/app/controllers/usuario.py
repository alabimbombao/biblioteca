"""Controlador de administración de usuarios."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.controllers.auth import revocar_tokens
from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from app.core.security import hashear_password
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.usuario import (
    ActivoActualizar,
    RolActualizar,
    UsuarioCrear,
)


def listar_usuarios(
    db: Session,
    skip: int,
    limit: int,
    rol: RolUsuario | None,
    activo: bool | None,
) -> tuple[list[Usuario], int]:
    """Devuelve una página de usuarios y el total."""
    filtros = []
    if rol is not None:
        filtros.append(Usuario.rol == rol)
    if activo is not None:
        filtros.append(Usuario.activo == activo)

    consulta = select(Usuario).where(*filtros)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    items = db.scalars(
        consulta.order_by(Usuario.id).offset(skip).limit(limit)
    ).all()
    return list(items), total


def obtener_usuario(db: Session, usuario_id: int) -> Usuario:
    """Busca un usuario o lanza 404."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise NoEncontrado(f"Usuario {usuario_id} no encontrado")
    return usuario


def crear_usuario(db: Session, datos: UsuarioCrear) -> Usuario:
    """Crea un usuario con rol bibliotecario o admin."""
    email = str(datos.email).lower()

    existe_usuario = db.scalar(
        select(Usuario).where(Usuario.email == email)
    )
    existe_socio = db.scalar(select(Socio).where(Socio.email == email))
    if existe_usuario or existe_socio:
        raise Conflicto("Ya existe un usuario o socio con ese email")

    usuario = Usuario(
        email=email,
        nombre=datos.nombre,
        password_hash=hashear_password(datos.password),
        rol=RolUsuario(datos.rol),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_rol(
    db: Session,
    usuario_id: int,
    datos: RolActualizar,
    actual: Usuario,
) -> Usuario:
    """Cambia el rol de un usuario y revoca sus refresh tokens."""
    usuario = obtener_usuario(db, usuario_id)

    # Z5: un admin no puede quitarse su propio rol.
    if usuario.id == actual.id and datos.rol != RolUsuario.admin:
        raise ReglaNegocio("Un administrador no puede quitarse su propio rol")

    usuario.rol = datos.rol
    revocar_tokens(db, usuario.id)
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_activo(
    db: Session,
    usuario_id: int,
    datos: ActivoActualizar,
    actual: Usuario,
) -> Usuario:
    """Activa o desactiva un usuario y revoca sus tokens si se desactiva."""
    usuario = obtener_usuario(db, usuario_id)

    # Z5: un admin no puede desactivarse a sí mismo.
    if usuario.id == actual.id and not datos.activo:
        raise ReglaNegocio("Un administrador no puede desactivarse a sí mismo")

    usuario.activo = datos.activo
    if not datos.activo:
        revocar_tokens(db, usuario.id)

    db.commit()
    db.refresh(usuario)
    return usuario
