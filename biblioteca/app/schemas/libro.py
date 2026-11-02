"""Esquemas de libros."""

import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.autor import AutorOut
from app.schemas.categoria import CategoriaOut


class LibroBase(BaseModel):
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    autor_id: int

    @field_validator("titulo")
    @classmethod
    def limpiar_titulo(cls, valor: str) -> str:
        valor = " ".join(valor.split()).title()
        if not (1 <= len(valor) <= 150):
            raise ValueError("titulo debe tener entre 1 y 150 caracteres")
        return valor

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, valor: str) -> str:
        if len(valor) != 13 or not valor.isdigit():
            raise ValueError("isbn debe tener exactamente 13 digitos")
        return valor

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, valor: int) -> int:
        if not (1450 <= valor <= datetime.date.today().year):
            raise ValueError("anio_publicacion fuera de rango (1450-anio actual)")
        return valor

    @field_validator("ejemplares")
    @classmethod
    def validar_ejemplares(cls, valor: int) -> int:
        if not (1 <= valor <= 50):
            raise ValueError("ejemplares debe estar entre 1 y 50")
        return valor


class LibroCreate(LibroBase):
    """Datos para crear un libro."""

    categoria_ids: list[int] = Field(..., min_length=1, max_length=5)

    @field_validator("categoria_ids")
    @classmethod
    def sin_repetidos(cls, valor: list[int]) -> list[int]:
        if len(valor) != len(set(valor)):
            raise ValueError("categoria_ids no debe tener repetidos")
        return valor


class LibroUpdate(BaseModel):
    """Datos para actualizar un libro."""

    titulo: str | None = None
    anio_publicacion: int | None = None
    ejemplares: int | None = None
    categoria_ids: list[int] | None = None


class LibroOut(BaseModel):
    """Datos públicos de un libro."""

    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    autor: AutorOut
    categorias: list[CategoriaOut]

    model_config = {"from_attributes": True}
