"""Esquemas de autores."""

import datetime

from pydantic import BaseModel, Field, field_validator


class AutorBase(BaseModel):
    nombre: str = Field(..., description="Nombre completo del autor (2-100 caracteres)", examples=["Gabriel García Márquez"])
    nacionalidad: str | None = Field(None, description="Nacionalidad o país de origen", examples=["Colombiana"])
    anio_nacimiento: int | None = Field(None, description="Año de nacimiento (1000 al año actual)", examples=[1927])

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

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Gabriel García Márquez",
                "nacionalidad": "Colombiana",
                "anio_nacimiento": 1927,
            }
        }
    }


class AutorUpdate(BaseModel):
    """Datos para actualizar un autor."""

    nombre: str | None = Field(None, description="Nuevo nombre del autor", examples=["Gabriel García Márquez"])
    nacionalidad: str | None = Field(None, description="Nueva nacionalidad", examples=["Colombiana"])
    anio_nacimiento: int | None = Field(None, description="Nuevo año de nacimiento", examples=[1927])

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).title()
        return valor

    model_config = {
        "json_schema_extra": {
            "example": {
                "nacionalidad": "Colombiana",
                "anio_nacimiento": 1927,
            }
        }
    }


class AutorOut(AutorBase):
    """Datos públicos de un autor."""

    id: int

    model_config = {"from_attributes": True}
