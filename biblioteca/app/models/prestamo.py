"""Modelo de préstamos."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, false, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prestamo(Base):
    """Préstamo de un libro a un socio."""

    __tablename__ = "prestamos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id"), nullable=False)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    fecha_prestamo: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today
    )
    fecha_limite: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_devolucion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    multa: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    multa_pagada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    registrado_por_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    socio: Mapped[Optional["Socio"]] = relationship(
        "Socio", back_populates="prestamos"
    )
    libro: Mapped[Optional["Libro"]] = relationship(
        "Libro", back_populates="prestamos"
    )
    registrado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", back_populates="prestamos_registrados"
    )

    @property
    def estado(self) -> str:
        """Estado calculado del préstamo: activo, vencido o devuelto."""
        if self.fecha_devolucion is not None:
            return "devuelto"
        if self.fecha_limite < date.today():
            return "vencido"
        return "activo"
