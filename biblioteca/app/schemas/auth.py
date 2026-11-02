"""Esquemas de autenticación y registro."""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.socio import validar_telefono
from app.schemas.usuario import UsuarioRespuesta, validar_password_fuerte

__all__ = [
    "UsuarioRegistro",
    "UsuarioRespuesta",
    "TokenRespuesta",
    "RefreshSolicitud",
    "CambioPassword",
]


class UsuarioRegistro(BaseModel):
    """Registro público de un socio."""

    email: EmailStr
    nombre: str = Field(min_length=3, max_length=100)
    telefono: str | None = None
    password: str
    confirmar_password: str

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).lower()

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        return " ".join(valor.split()).title()

    @field_validator("telefono")
    @classmethod
    def validar_telefono_registro(cls, valor: str | None) -> str | None:
        return validar_telefono(valor)

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        return validar_password_fuerte(valor)

    @model_validator(mode="after")
    def validar_confirmacion(self):
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden")
        return self


class TokenRespuesta(BaseModel):
    """Par de tokens entregado por el login y el refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshSolicitud(BaseModel):
    """Refresh token enviado por el cliente."""

    refresh_token: str


class CambioPassword(BaseModel):
    """Cambio de contraseña del usuario autenticado."""

    password_actual: str
    password_nueva: str

    @field_validator("password_nueva")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        return validar_password_fuerte(valor)
