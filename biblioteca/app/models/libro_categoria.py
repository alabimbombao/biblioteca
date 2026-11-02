"""Tabla intermedia entre libros y categorías (relación muchos a muchos)."""

from sqlalchemy import Column, ForeignKey, Integer, Table

from app.core.database import Base

libro_categoria = Table(
    "libro_categoria",
    Base.metadata,
    Column("libro_id", Integer, ForeignKey("libros.id"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("categorias.id"), primary_key=True),
)
