"""Controlador de autenticación: registro, login y tokens."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    Conflicto,
    CuentaBloqueada,
    NoAutenticado,
    Prohibido,
    ReglaNegocio,
)
from app.core.security import (
    crear_token,
    decodificar_token,
    hashear_password,
    verificar_password,
)
from app.models.refresh_token import RefreshToken
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import CambioPassword, UsuarioRegistro

MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


def _ahora() -> datetime:
    """Fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def _con_zona(valor: datetime | None) -> datetime | None:
    """Normaliza una fecha para poder compararla siempre en UTC."""
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def revocar_tokens(db: Session, usuario_id: int) -> None:
    """Revoca todos los refresh tokens vigentes de un usuario."""
    tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.usuario_id == usuario_id,
            RefreshToken.revocado.is_(False),
        )
    ).all()
    for token in tokens:
        token.revocado = True


def _emitir_tokens(db: Session, usuario: Usuario) -> dict:
    """Crea el access token, el refresh token y registra el jti."""
    configuracion = get_settings()
    duracion_access = timedelta(minutes=configuracion.access_token_expire_minutes)
    duracion_refresh = timedelta(days=configuracion.refresh_token_expire_days)

    access_token, _ = crear_token(usuario, "access", duracion_access)
    refresh_token, jti = crear_token(usuario, "refresh", duracion_refresh)

    db.add(
        RefreshToken(
            jti=jti,
            usuario_id=usuario.id,
            expira_en=_ahora() + duracion_refresh,
        )
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(duracion_access.total_seconds()),
    }


def registrar(db: Session, datos: UsuarioRegistro) -> Usuario:
    """Registra un socio y su usuario en una sola transacción."""
    email = str(datos.email).lower()

    existe_usuario = db.scalar(
        select(Usuario).where(Usuario.email == email)
    )
    existe_socio = db.scalar(select(Socio).where(Socio.email == email))
    if existe_usuario or existe_socio:
        raise Conflicto("Ya existe un usuario o socio con ese email")

    try:
        socio = Socio(
            nombre=datos.nombre,
            email=email,
            telefono=datos.telefono,
        )
        db.add(socio)
        db.flush()

        usuario = Usuario(
            email=email,
            nombre=datos.nombre,
            password_hash=hashear_password(datos.password),
            rol=RolUsuario.socio,
            socio_id=socio.id,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    except Exception:
        db.rollback()
        raise

    return usuario


def iniciar_sesion(db: Session, email: str, password: str) -> dict:
    """Valida las credenciales y entrega un par de tokens."""
    email = email.strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    ahora = _ahora()

    if usuario is not None:
        bloqueo = _con_zona(usuario.bloqueado_hasta)
        if bloqueo is not None and bloqueo > ahora:
            raise CuentaBloqueada("Cuenta bloqueada temporalmente")
        if bloqueo is not None and bloqueo <= ahora:
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            db.commit()

    # El mismo mensaje si el email no existe o la contraseña es incorrecta.
    if usuario is None or not verificar_password(password, usuario.password_hash):
        if usuario is not None:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
                usuario.bloqueado_hasta = ahora + timedelta(
                    minutes=MINUTOS_BLOQUEO
                )
            db.commit()
        raise NoAutenticado("Credenciales inválidas")

    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    db.refresh(usuario)

    return _emitir_tokens(db, usuario)


def refrescar(db: Session, refresh_token: str) -> dict:
    """Rota el refresh token y devuelve un par nuevo."""
    payload = decodificar_token(refresh_token, "refresh")
    jti = payload.get("jti")

    registro = db.scalar(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    if registro is None:
        raise NoAutenticado("Refresh token inválido")

    # Si se reutiliza un token ya rotado, se revocan todos los del usuario.
    if registro.revocado:
        revocar_tokens(db, registro.usuario_id)
        db.commit()
        raise NoAutenticado("Refresh token inválido")

    expira_en = _con_zona(registro.expira_en)
    if expira_en is not None and expira_en <= _ahora():
        raise NoAutenticado("Refresh token vencido")

    usuario = db.get(Usuario, registro.usuario_id)
    if usuario is None:
        raise NoAutenticado("Refresh token inválido")
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    registro.revocado = True
    db.commit()

    return _emitir_tokens(db, usuario)


def cerrar_sesion(db: Session, refresh_token: str) -> None:
    """Revoca el refresh token entregado por el cliente."""
    payload = decodificar_token(refresh_token, "refresh")

    registro = db.scalar(
        select(RefreshToken).where(RefreshToken.jti == payload.get("jti"))
    )
    if registro is None:
        raise NoAutenticado("Refresh token inválido")

    registro.revocado = True
    db.commit()


def cambiar_password(
    db: Session, usuario: Usuario, datos: CambioPassword
) -> None:
    """Cambia la contraseña y revoca todos los refresh tokens."""
    if not verificar_password(datos.password_actual, usuario.password_hash):
        raise ReglaNegocio("La contraseña actual no es correcta")

    if verificar_password(datos.password_nueva, usuario.password_hash):
        raise ReglaNegocio("La nueva contraseña debe ser diferente a la actual")

    usuario.password_hash = hashear_password(datos.password_nueva)
    revocar_tokens(db, usuario.id)
    db.commit()
