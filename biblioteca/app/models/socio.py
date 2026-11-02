"""Modelo de socios de la biblioteca."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Socio(Base):
    """Persona inscrita en la biblioteca."""

    __tablename__ = "socios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    fecha_alta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    prestamos: Mapped[list["Prestamo"]] = relationship(
        "Prestamo", back_populates="socio"
    )
    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", back_populates="socio", uselist=False
    )
