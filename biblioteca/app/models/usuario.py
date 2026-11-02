"""Modelo de usuarios del sistema."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RolUsuario(str, enum.Enum):
    """Roles disponibles en el sistema."""

    admin = "admin"
    bibliotecario = "bibliotecario"
    socio = "socio"


class Usuario(Base):
    """Usuario que inicia sesión en la API."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(
            RolUsuario,
            name="rolusuario",
            values_callable=lambda valores: [valor.value for valor in valores],
        ),
        default=RolUsuario.socio,
        server_default=RolUsuario.socio.value,
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    intentos_fallidos: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    socio_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("socios.id"), unique=True, nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    socio: Mapped[Optional["Socio"]] = relationship(
        "Socio", back_populates="usuario"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    prestamos_registrados: Mapped[list["Prestamo"]] = relationship(
        "Prestamo", back_populates="registrado_por"
    )
