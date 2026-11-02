"""Esquemas de autores."""

import datetime

from pydantic import BaseModel, field_validator


class AutorBase(BaseModel):
    nombre: str
    nacionalidad: str | None = None
    anio_nacimiento: int | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.split()).title()
        if not (2 <= len(valor) <= 100):
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("anio_nacimiento")
    @classmethod
    def validar_anio(cls, valor: int | None) -> int | None:
        if valor is not None and not (1000 <= valor <= datetime.date.today().year):
            raise ValueError("anio_nacimiento fuera de rango")
        return valor


class AutorCreate(AutorBase):
    """Datos para crear un autor."""


class AutorUpdate(BaseModel):
    """Datos para actualizar un autor."""

    nombre: str | None = None
    nacionalidad: str | None = None
    anio_nacimiento: int | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor


class AutorOut(AutorBase):
    """Datos públicos de un autor."""

    id: int

    model_config = {"from_attributes": True}
