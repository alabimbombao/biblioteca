from fastapi import APIRouter
from typing import List
from app.core.dependencies import SessionDep
from app.schemas.reportes import (
    LibroMasPrestado,
    CategoriaTotalLibros,
    PrestamoVencido,
    SocioConMulta,
    AutorReporte,
    ResumenBiblioteca,
)
import app.controllers.reportes as ctrl

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/libros-mas-prestados", response_model=List[LibroMasPrestado])
def libros_mas_prestados(db: SessionDep, limite: int = 5):
    return ctrl.libros_mas_prestados(db, limite)


@router.get("/categorias", response_model=List[CategoriaTotalLibros])
def categorias(db: SessionDep):
    return ctrl.categorias_total_libros(db)


@router.get("/prestamos-vencidos", response_model=List[PrestamoVencido])
def prestamos_vencidos(db: SessionDep):
    return ctrl.prestamos_vencidos(db)


@router.get("/socios-con-multas", response_model=List[SocioConMulta])
def socios_con_multas(db: SessionDep):
    return ctrl.socios_con_multas(db)


@router.get("/autores", response_model=List[AutorReporte])
def autores(db: SessionDep):
    return ctrl.reporte_autores(db)


@router.get("/resumen", response_model=ResumenBiblioteca)
def resumen(db: SessionDep):
    return ctrl.resumen_biblioteca(db)
