"""Esquemas de categorías."""

from pydantic import BaseModel, Field, field_validator


class CategoriaBase(BaseModel):
    nombre: str = Field(..., description="Nombre de la categoría (3-50 caracteres)", examples=["novela historica"])
    descripcion: str | None = Field(None, description="Descripción del género literario", examples=["Obras narrativas basadas en eventos históricos"])

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.split()).lower()
        if not (3 <= len(valor) <= 50):
            raise ValueError("nombre debe tener entre 3 y 50 caracteres")
        return valor


class CategoriaCreate(CategoriaBase):
    """Datos para crear una categoría."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "novela historica",
                "descripcion": "Obras narrativas ambientadas en periodos o sucesos históricos reales",
            }
        }
    }


class CategoriaUpdate(BaseModel):
    """Datos para actualizar una categoría."""

    nombre: str | None = Field(None, description="Nuevo nombre de la categoría", examples=["ficcion historica"])
    descripcion: str | None = Field(None, description="Nueva descripción", examples=["Narrativa y crónicas históricas"])

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is not None:
            return " ".join(valor.split()).lower()
        return valor

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "ficcion historica",
                "descripcion": "Narrativa y crónicas históricas",
            }
        }
    }


class CategoriaOut(CategoriaBase):
    """Datos públicos de una categoría."""

    id: int

    model_config = {"from_attributes": True}
