from datetime import date
from sqlalchemy import Column, Date, Numeric, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    fecha_prestamo = Column(Date, nullable=False, default=date.today)
    fecha_limite = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=True)
    multa = Column(Numeric(10, 2), nullable=False, default=0)

    socio = relationship("Socio", back_populates="prestamos")
    libro = relationship("Libro", back_populates="prestamos")
