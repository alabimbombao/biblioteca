"""Ruta de salud de la API."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.dependencies import SessionDep
from app.core.exceptions import ServicioNoDisponible

router = APIRouter(tags=["Salud"])


@router.get(
    "/health",
    summary="Estado de la API y de la base de datos",
    responses={503: {"description": "La base de datos no responde"}},
)
def salud(db: SessionDep):
    """Comprueba que la API y PostgreSQL respondan."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServicioNoDisponible("Base de datos no disponible") from exc

    return {"status": "ok", "database": "ok"}
