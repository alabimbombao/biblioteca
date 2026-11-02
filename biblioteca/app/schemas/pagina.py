"""Esquema genérico de respuesta paginada."""

from pydantic import BaseModel


class Pagina[T](BaseModel):
    """Respuesta paginada: items, total, skip y limit."""

    items: list[T]
    total: int
    skip: int
    limit: int
