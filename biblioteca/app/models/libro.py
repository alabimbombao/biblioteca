"""Modelo de libros."""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, inspect as sa_inspect, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.libro_categoria import libro_categoria


class Libro(Base):
    """Libro disponible en la biblioteca."""

    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, nullable=False)
    anio_publicacion: Mapped[int] = mapped_column(Integer, nullable=False)
    ejemplares: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    autor_id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"), nullable=False
    )
    portada_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, default=None
    )
    portada_public_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, default=None
    )

    autor: Mapped[Optional["Autor"]] = relationship(
        "Autor", back_populates="libros"
    )
    categorias: Mapped[list["Categoria"]] = relationship(
        "Categoria",
        secondary=libro_categoria,
        back_populates="libros",
    )
    prestamos: Mapped[list["Prestamo"]] = relationship(
        "Prestamo", back_populates="libro"
    )

    @property
    def disponibles(self) -> int:
        """Cantidad de ejemplares que no están prestados.

        1. Si el controlador ya calculó el valor, se reutiliza.
        2. Si la relación de préstamos está cargada, se calcula.
        3. Si no, se devuelve el total de ejemplares.
        """
        valor = self.__dict__.get("_disponibles")
        if valor is not None:
            return valor

        estado = sa_inspect(self)
        if "prestamos" not in estado.unloaded:
            activos = sum(
                1 for prestamo in self.prestamos
                if prestamo.fecha_devolucion is None
            )
            return self.ejemplares - activos

        return self.ejemplares

    @disponibles.setter
    def disponibles(self, valor: int) -> None:
        """Permite que el controlador asigne el valor calculado por SQL."""
        self.__dict__["_disponibles"] = valor
