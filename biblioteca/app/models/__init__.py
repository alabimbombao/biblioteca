"""Importa todos los modelos para que Alembic los detecte.

El orden importa: primero la tabla intermedia y las entidades base.
"""

from app.models import libro_categoria  # noqa: F401
from app.models.autor import Autor  # noqa: F401
from app.models.categoria import Categoria  # noqa: F401
from app.models.libro import Libro  # noqa: F401
from app.models.socio import Socio  # noqa: F401
from app.models.usuario import RolUsuario, Usuario  # noqa: F401
from app.models.prestamo import Prestamo  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

__all__ = [
    "Autor",
    "Categoria",
    "Libro",
    "Socio",
    "Usuario",
    "RolUsuario",
    "Prestamo",
    "RefreshToken",
]
