import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class SocioBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        return " ".join(v.split()).title()

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not (7 <= len(v) <= 15):
                raise ValueError("telefono debe tener entre 7 y 15 caracteres")
            if not re.match(r"^[\d\s+]+$", v):
                raise ValueError("telefono solo puede contener digitos, espacios o +")
        return v


class SocioCreate(SocioBase):
    pass


class SocioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).title()
        return v


class SocioOut(SocioBase):
    id: int
    activo: bool
    fecha_alta: datetime

    model_config = {"from_attributes": True}
