"""Esquemas de usuarios y reglas de contraseña."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import RolUsuario


def validar_password_fuerte(valor: str) -> str:
    """Valida la longitud mínima de una contraseña (mínimo 8 caracteres)."""
    if not (8 <= len(valor) <= 64):
        raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
    return valor


class UsuarioRespuesta(BaseModel):
    """Datos públicos de un usuario (nunca incluye la contraseña)."""

    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    activo: bool
    socio_id: int | None
    creado_en: datetime

    model_config = {"from_attributes": True}


class UsuarioCrear(BaseModel):
    """Datos para que un administrador cree un usuario del staff."""

    email: EmailStr
    nombre: str = Field(min_length=3, max_length=100)
    password: str
    rol: Literal["bibliotecario", "admin"]

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).lower()

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        return " ".join(valor.split()).title()

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        return validar_password_fuerte(valor)


class RolActualizar(BaseModel):
    """Nuevo rol para un usuario."""

    rol: RolUsuario


class ActivoActualizar(BaseModel):
    """Nuevo estado de actividad para un usuario."""

    activo: bool
