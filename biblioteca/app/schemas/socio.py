"""Esquemas de socios."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


def validar_telefono(valor: str | None) -> str | None:
    """Valida el formato del teléfono usado en el Taller 1."""
    if valor is not None:
        if not (7 <= len(valor) <= 15):
            raise ValueError("telefono debe tener entre 7 y 15 caracteres")
        if not re.match(r"^[\d\s+]+$", valor):
            raise ValueError("telefono solo puede contener digitos, espacios o +")
    return valor


class SocioBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        return " ".join(valor.split()).title()

    @field_validator("email")
    @classmethod
    def lower_email(cls, valor: EmailStr) -> str:
        return str(valor).lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono_socio(cls, valor: str | None) -> str | None:
        return validar_telefono(valor)


class SocioCreate(SocioBase):
    """Datos para crear un socio desde el staff."""


class SocioUpdate(BaseModel):
    """Datos que el staff puede modificar de un socio."""

    nombre: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor


class SocioActualizarPropio(BaseModel):
    """Un socio solo puede cambiar su nombre y su teléfono."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    telefono: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor

    @field_validator("telefono")
    @classmethod
    def validar_telefono_propio(cls, valor: str | None) -> str | None:
        return validar_telefono(valor)


class SocioOut(SocioBase):
    """Datos públicos de un socio."""

    id: int
    activo: bool
    fecha_alta: datetime

    model_config = {"from_attributes": True}
