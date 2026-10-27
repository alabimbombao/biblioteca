from pydantic import BaseModel, field_validator
from typing import Optional


class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        v = " ".join(v.split()).lower()
        if not (3 <= len(v) <= 50):
            raise ValueError("nombre debe tener entre 3 y 50 caracteres")
        return v


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).lower()
        return v


class CategoriaOut(CategoriaBase):
    id: int

    model_config = {"from_attributes": True}
