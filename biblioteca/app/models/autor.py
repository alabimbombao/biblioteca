"""Modelo de autores."""

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Autor(Base):
    """Autor de uno o varios libros."""

    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nacionalidad: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    anio_nacimiento: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    libros: Mapped[list["Libro"]] = relationship(
        "Libro", back_populates="autor"
    )
