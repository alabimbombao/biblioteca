"""Esquemas de categorías."""

from pydantic import BaseModel, field_validator


class CategoriaBase(BaseModel):
    nombre: str
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.split()).lower()
        if not (3 <= len(valor) <= 50):
            raise ValueError("nombre debe tener entre 3 y 50 caracteres")
        return valor


class CategoriaCreate(CategoriaBase):
    """Datos para crear una categoría."""


class CategoriaUpdate(BaseModel):
    """Datos para actualizar una categoría."""

    nombre: str | None = None
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).lower()
        return valor


class CategoriaOut(CategoriaBase):
    """Datos públicos de una categoría."""

    id: int

    model_config = {"from_attributes": True}
