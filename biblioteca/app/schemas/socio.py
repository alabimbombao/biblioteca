"""Esquemas de socios."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


def validar_telefono(valor: str | None) -> str | None:
    """Valida el formato del teléfono usado en el Taller 1."""
    if valor is not None:
        if not (7 <= len(valor) <= 15):
            raise ValueError("telefono debe tener entre 7 y 15 caracteres")
        if not re.match(r"^[\d\s+]+$", valor):
            raise ValueError("telefono solo puede contener digitos, espacios o +")
    return valor


class SocioBase(BaseModel):
    nombre: str = Field(..., description="Nombre completo del socio", examples=["Ana Torres"])
    email: EmailStr = Field(..., description="Correo electrónico único del socio", examples=["ana.torres@example.com"])
    telefono: str | None = Field(None, description="Número de teléfono (7-15 caracteres, dígitos o +)", examples=["+57 3001234567"])

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

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Ana Torres",
                "email": "ana.torres@example.com",
                "telefono": "+57 3001234567",
            }
        }
    }


class SocioUpdate(BaseModel):
    """Datos que el staff puede modificar de un socio."""

    nombre: str | None = Field(None, description="Nuevo nombre del socio", examples=["Ana Torres"])
    email: EmailStr | None = Field(None, description="Nuevo correo electrónico", examples=["ana.torres@example.com"])
    telefono: str | None = Field(None, description="Nuevo teléfono", examples=["+57 3001234567"])

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor

    @field_validator("telefono")
    @classmethod
    def validar_telefono_socio(cls, valor: str | None) -> str | None:
        return validar_telefono(valor)

    model_config = {
        "json_schema_extra": {
            "example": {
                "telefono": "+57 3009998877",
            }
        }
    }


class SocioActualizarPropio(BaseModel):
    """Un socio solo puede cambiar su nombre y su teléfono."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(None, description="Nuevo nombre", examples=["Ana Torres"])
    telefono: str | None = Field(None, description="Nuevo teléfono", examples=["+57 3001234567"])

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor

    @field_validator("telefono")
    @classmethod
    def validar_telefono_socio(cls, valor: str | None) -> str | None:
        return validar_telefono(valor)


class SocioOut(SocioBase):
    """Datos públicos de un socio."""

    id: int
    activo: bool
    fecha_alta: datetime

    model_config = {"from_attributes": True}
