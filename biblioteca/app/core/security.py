"""Hash de contraseñas y creación/lectura de JSON Web Tokens."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.exceptions import NoAutenticado

if TYPE_CHECKING:  # pragma: no cover
    from app.models.usuario import Usuario

# Argon2 es el algoritmo recomendado por pwdlib.
password_hash = PasswordHash.recommended()


def hashear_password(password: str) -> str:
    """Devuelve el hash Argon2 de una contraseña."""
    return password_hash.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    """Comprueba una contraseña contra su hash Argon2."""
    try:
        return password_hash.verify(password, hash_guardado)
    except Exception:
        return False


def crear_token(usuario: "Usuario", tipo: str, duracion: timedelta) -> tuple[str, str]:
    """Crea un JWT y devuelve el token junto con su identificador jti."""
    configuracion = get_settings()
    ahora = datetime.now(timezone.utc)
    jti = str(uuid4())
    payload = {
        "sub": str(usuario.id),
        "rol": usuario.rol.value,
        "type": tipo,
        "iat": ahora,
        "exp": ahora + duracion,
        "jti": jti,
    }
    token = jwt.encode(
        payload,
        configuracion.secret_key,
        algorithm=configuracion.algorithm,
    )
    return token, jti


def decodificar_token(token: str, tipo_esperado: str | None = None) -> dict:
    """Valida la firma y el vencimiento de un JWT.

    Siempre se pasa la lista ``algorithms``; nunca se confía en el
    algoritmo que declara el propio token.
    """
    configuracion = get_settings()
    try:
        payload = jwt.decode(
            token,
            configuracion.secret_key,
            algorithms=[configuracion.algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise NoAutenticado("Token inválido o vencido") from exc

    if tipo_esperado is not None and payload.get("type") != tipo_esperado:
        raise NoAutenticado("Tipo de token inválido")

    return payload
