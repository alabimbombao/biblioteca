"""Rutas de reportes (solo staff)."""

from fastapi import APIRouter

from app.controllers import reportes as ctrl
from app.core.dependencies import SessionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.routes.respuestas import RESPUESTAS_STAFF
from app.schemas.reportes import (
    AutorReporte,
    CategoriaTotalLibros,
    LibroMasPrestado,
    PrestamoVencido,
    ResumenBiblioteca,
    SocioConMulta,
)

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
)


@router.get(
    "/libros-mas-prestados",
    response_model=list[LibroMasPrestado],
    summary="Libros más prestados",
    responses=RESPUESTAS_STAFF,
)
def libros_mas_prestados(db: SessionDep, limite: int = 5):
    """Libros ordenados por cantidad de préstamos."""
    return ctrl.libros_mas_prestados(db, limite)


@router.get(
    "/categorias",
    response_model=list[CategoriaTotalLibros],
    summary="Total de libros por categoría",
    responses=RESPUESTAS_STAFF,
)
def categorias(db: SessionDep):
    """Cantidad de libros por categoría."""
    return ctrl.categorias_total_libros(db)


@router.get(
    "/prestamos-vencidos",
    response_model=list[PrestamoVencido],
    summary="Préstamos vencidos",
    responses=RESPUESTAS_STAFF,
)
def prestamos_vencidos(db: SessionDep):
    """Préstamos vencidos con sus días de retraso."""
    return ctrl.prestamos_vencidos(db)


@router.get(
    "/socios-con-multas",
    response_model=list[SocioConMulta],
    summary="Socios con multas",
    responses=RESPUESTAS_STAFF,
)
def socios_con_multas(db: SessionDep):
    """Socios con multas acumuladas."""
    return ctrl.socios_con_multas(db)


@router.get(
    "/autores",
    response_model=list[AutorReporte],
    summary="Reporte por autor",
    responses=RESPUESTAS_STAFF,
)
def autores(db: SessionDep):
    """Totales de libros, ejemplares y préstamos por autor."""
    return ctrl.reporte_autores(db)


@router.get(
    "/resumen",
    response_model=ResumenBiblioteca,
    summary="Resumen de la biblioteca",
    responses=RESPUESTAS_STAFF,
)
def resumen(db: SessionDep):
    """Totales generales de la biblioteca."""
    return ctrl.resumen_biblioteca(db)
