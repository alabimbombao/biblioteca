import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
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
    def limpiar_titulo(cls, v: str) -> str:
        v = " ".join(v.split()).title()
        if not (1 <= len(v) <= 150):
            raise ValueError("titulo debe tener entre 1 y 150 caracteres")
        return v

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, v: str) -> str:
        if len(v) != 13 or not v.isdigit():
            raise ValueError("isbn debe tener exactamente 13 digitos")
        return v

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        if not (1450 <= v <= datetime.date.today().year):
            raise ValueError("anio_publicacion fuera de rango (1450-anio actual)")
        return v

    @field_validator("ejemplares")
    @classmethod
    def validar_ejemplares(cls, v: int) -> int:
        if not (1 <= v <= 50):
            raise ValueError("ejemplares debe estar entre 1 y 50")
        return v


class LibroCreate(LibroBase):
    categoria_ids: List[int] = Field(..., min_length=1, max_length=5)

    @field_validator("categoria_ids")
    @classmethod
    def sin_repetidos(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("categoria_ids no debe tener repetidos")
        return v


class LibroUpdate(BaseModel):
    titulo: Optional[str] = None
    anio_publicacion: Optional[int] = None
    ejemplares: Optional[int] = None
    categoria_ids: Optional[List[int]] = None


class LibroOut(BaseModel):
    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    autor: AutorOut
    categorias: List[CategoriaOut]

    model_config = {"from_attributes": True}
