from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Socio(Base):
    __tablename__ = "socios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(15), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_alta = Column(DateTime, server_default=func.now(), nullable=False)

    prestamos = relationship("Prestamo", back_populates="socio")
