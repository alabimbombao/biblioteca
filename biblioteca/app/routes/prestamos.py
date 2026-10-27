from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.prestamo import PrestamoCreate, PrestamoDevolucion, PrestamoOut
import app.controllers.prestamos as ctrl

router = APIRouter(prefix="/prestamos", tags=["Prestamos"])


@router.get("/", response_model=List[PrestamoOut])
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    estado: Optional[str] = None,
    socio_id: Optional[int] = None,
    libro_id: Optional[int] = None,
):
    return ctrl.listar_prestamos(db, pag.skip, pag.limit, estado, socio_id, libro_id)


@router.get("/{prestamo_id}", response_model=PrestamoOut)
def obtener(prestamo_id: int, db: SessionDep):
    return ctrl.obtener_prestamo(db, prestamo_id)


@router.post("/", response_model=PrestamoOut, status_code=201)
def crear(datos: PrestamoCreate, db: SessionDep):
    return ctrl.crear_prestamo(db, datos)


@router.post("/{prestamo_id}/devolucion", response_model=PrestamoOut)
def devolver(prestamo_id: int, datos: PrestamoDevolucion, db: SessionDep):
    return ctrl.devolver_prestamo(db, prestamo_id, datos)
