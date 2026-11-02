"""Modelo de categorías y tabla intermedia con libros."""

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.libro_categoria import libro_categoria


class Categoria(Base):
    """Categoría temática de los libros."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    libros: Mapped[list["Libro"]] = relationship(
        "Libro",
        secondary=libro_categoria,
        back_populates="categorias",
    )
