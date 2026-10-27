from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.socio import SocioCreate, SocioUpdate, SocioOut
from app.schemas.prestamo import PrestamoOut
import app.controllers.socios as ctrl

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.get("/", response_model=List[SocioOut])
def listar(pag: PaginacionDep, db: SessionDep, activo: Optional[bool] = None):
    return ctrl.listar_socios(db, pag.skip, pag.limit, activo)


@router.get("/{socio_id}", response_model=SocioOut)
def obtener(socio_id: int, db: SessionDep):
    return ctrl.obtener_socio(db, socio_id)


@router.post("/", response_model=SocioOut, status_code=201)
def crear(datos: SocioCreate, db: SessionDep):
    return ctrl.crear_socio(db, datos)


@router.patch("/{socio_id}", response_model=SocioOut)
def actualizar(socio_id: int, datos: SocioUpdate, db: SessionDep):
    return ctrl.actualizar_socio(db, socio_id, datos)


@router.delete("/{socio_id}", status_code=204)
def eliminar(socio_id: int, db: SessionDep):
    ctrl.eliminar_socio(db, socio_id)


@router.get("/{socio_id}/prestamos", response_model=List[PrestamoOut])
def prestamos_del_socio(
    socio_id: int,
    pag: PaginacionDep,
    db: SessionDep,
    estado: Optional[str] = None,
):
    return ctrl.prestamos_de_socio(db, socio_id, pag.skip, pag.limit, estado)
