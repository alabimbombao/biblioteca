"""Esquemas de libros."""

import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.autor import AutorOut
from app.schemas.categoria import CategoriaOut


class LibroBase(BaseModel):
    titulo: str = Field(..., description="Título del libro (1-150 caracteres)", examples=["Cien Años de Soledad"])
    isbn: str = Field(..., description="Código ISBN de 13 dígitos numéricos", examples=["9788437604947"])
    anio_publicacion: int = Field(..., description="Año de publicación (1450 al año actual)", examples=[1967])
    ejemplares: int = Field(..., description="Total de ejemplares físicos disponibles (1-50)", examples=[5])
    autor_id: int = Field(..., description="ID del autor existente (ver /autores)", examples=[1])

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

    categoria_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Lista de IDs de categorías asignadas (entre 1 y 5 categorías)",
        examples=[[1, 2]],
    )

    @field_validator("categoria_ids")
    @classmethod
    def sin_repetidos(cls, valor: list[int]) -> list[int]:
        if len(valor) != len(set(valor)):
            raise ValueError("categoria_ids no debe tener repetidos")
        return valor

    model_config = {
        "json_schema_extra": {
            "example": {
                "titulo": "Cien Años de Soledad",
                "isbn": "9788437604947",
                "anio_publicacion": 1967,
                "ejemplares": 5,
                "autor_id": 1,
                "categoria_ids": [1, 2],
            }
        }
    }


class LibroUpdate(BaseModel):
    """Datos para actualizar un libro."""

    titulo: str | None = Field(None, description="Nuevo título", examples=["Cien Años de Soledad (Edición Especial)"])
    anio_publicacion: int | None = Field(None, description="Nuevo año de publicación", examples=[1967])
    ejemplares: int | None = Field(None, description="Nuevo número total de ejemplares", examples=[8])
    categoria_ids: list[int] | None = Field(None, description="Nueva lista de IDs de categorías", examples=[[1, 3]])

    model_config = {
        "json_schema_extra": {
            "example": {
                "titulo": "Cien Años de Soledad (Edición Especial)",
                "ejemplares": 8,
                "categoria_ids": [1, 3],
            }
        }
    }


class LibroOut(BaseModel):
    """Datos públicos de un libro."""

    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    portada_url: str | None = None
    autor: AutorOut
    categorias: list[CategoriaOut]

    model_config = {"from_attributes": True}
