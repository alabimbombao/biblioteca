import datetime
from pydantic import BaseModel, field_validator
from typing import Optional


class AutorBase(BaseModel):
    nombre: str
    nacionalidad: Optional[str] = None
    anio_nacimiento: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        v = " ".join(v.split()).title()
        if not (2 <= len(v) <= 100):
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return v

    @field_validator("anio_nacimiento")
    @classmethod
    def validar_anio(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1000 <= v <= datetime.date.today().year):
            raise ValueError("anio_nacimiento fuera de rango")
        return v


class AutorCreate(AutorBase):
    pass


class AutorUpdate(BaseModel):
    nombre: Optional[str] = None
    nacionalidad: Optional[str] = None
    anio_nacimiento: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).title()
        return v


class AutorOut(AutorBase):
    id: int

    model_config = {"from_attributes": True}
