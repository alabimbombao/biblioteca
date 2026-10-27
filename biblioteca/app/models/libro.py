from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import inspect as sa_inspect
from app.core.database import Base
from app.models.libro_categoria import libro_categoria


class Libro(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    isbn = Column(String(13), unique=True, nullable=False)
    anio_publicacion = Column(Integer, nullable=False)
    ejemplares = Column(Integer, nullable=False, default=1)
    autor_id = Column(Integer, ForeignKey("autores.id"), nullable=False)

    autor = relationship("Autor", back_populates="libros")
    categorias = relationship(
        "Categoria", secondary=libro_categoria, back_populates="libros"
    )
    prestamos = relationship("Prestamo", back_populates="libro")

    @property
    def disponibles(self) -> int:
        """Devuelve disponibles:
        1. Si _enriquecer ya lo asignó, usa ese valor.
        2. Si la relación prestamos está cargada, lo calcula.
        3. Fallback: devuelve ejemplares.
        """
        # _enriquecer del controller asigna el valor en __dict__
        val = self.__dict__.get("_disponibles")
        if val is not None:
            return val
        # Si prestamos está cargado en la sesión, calcular
        state = sa_inspect(self)
        if "prestamos" not in state.unloaded:
            activos = sum(1 for p in self.prestamos if p.fecha_devolucion is None)
            return self.ejemplares - activos
        # Fallback conservador
        return self.ejemplares

    @disponibles.setter
    def disponibles(self, value: int) -> None:
        """Permite que _enriquecer asigne el valor calculado por SQL."""
        self.__dict__["_disponibles"] = value
