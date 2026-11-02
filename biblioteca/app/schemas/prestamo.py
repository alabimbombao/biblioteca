"""Esquemas de préstamos y multas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.libro import LibroOut
from app.schemas.socio import SocioOut


class PrestamoCreate(BaseModel):
    """Datos para registrar un préstamo."""

    socio_id: int
    libro_id: int
    fecha_prestamo: date | None = None
    dias: int = 14

    @field_validator("dias")
    @classmethod
    def validar_dias(cls, valor: int) -> int:
        if not (1 <= valor <= 30):
            raise ValueError("dias debe estar entre 1 y 30")
        return valor


class PrestamoDevolucion(BaseModel):
    """Datos para registrar una devolución."""

    fecha_devolucion: date | None = None


class PrestamoOut(BaseModel):
    """Datos públicos de un préstamo."""

    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: date | None = None
    multa: Decimal
    multa_pagada: bool
    registrado_por_id: int | None = None
    estado: str
    socio: SocioOut | None = None
    libro: LibroOut | None = None

    model_config = {"from_attributes": True}


class MultasSocio(BaseModel):
    """Multas pendientes de pago del socio autenticado."""

    items: list[PrestamoOut]
    total_adeudado: Decimal
