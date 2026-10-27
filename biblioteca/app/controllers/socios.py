from datetime import date
from sqlalchemy.orm import Session, selectinload
from app.models.socio import Socio
from app.models.prestamo import Prestamo
from app.schemas.socio import SocioCreate, SocioUpdate
from app.core.exceptions import Conflicto, NoEncontrado
from typing import Optional


def listar_socios(db: Session, skip: int, limit: int, activo: Optional[bool]):
    q = db.query(Socio)
    if activo is not None:
        q = q.filter(Socio.activo == activo)
    return q.offset(skip).limit(limit).all()


def obtener_socio(db: Session, socio_id: int) -> Socio:
    socio = db.get(Socio, socio_id)
    if not socio:
        raise NoEncontrado(f"Socio {socio_id} no encontrado")
    return socio


def crear_socio(db: Session, datos: SocioCreate) -> Socio:
    if db.query(Socio).filter(Socio.email == datos.email).first():
        raise Conflicto(f"Ya existe un socio con email '{datos.email}'")
    socio = Socio(**datos.model_dump())
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def actualizar_socio(db: Session, socio_id: int, datos: SocioUpdate) -> Socio:
    socio = obtener_socio(db, socio_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "email" in cambios and cambios["email"] != socio.email:
        if db.query(Socio).filter(Socio.email == cambios["email"]).first():
            raise Conflicto(f"Ya existe un socio con email '{cambios['email']}'")
    for k, v in cambios.items():
        setattr(socio, k, v)
    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio(db: Session, socio_id: int) -> None:
    socio = obtener_socio(db, socio_id)
    tiene_historial = db.query(Prestamo).filter(Prestamo.socio_id == socio_id).first()
    if tiene_historial:
        # Borrado logico: solo desactivar
        socio.activo = False
        db.commit()
    else:
        db.delete(socio)
        db.commit()


def prestamos_de_socio(
    db: Session, socio_id: int, skip: int, limit: int, estado: Optional[str]
):
    obtener_socio(db, socio_id)  # verifica existencia
    hoy = date.today()
    q = (
        db.query(Prestamo)
        .options(selectinload(Prestamo.libro), selectinload(Prestamo.socio))
        .filter(Prestamo.socio_id == socio_id)
    )
    if estado == "activo":
        q = q.filter(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite >= hoy,
        )
    elif estado == "vencido":
        q = q.filter(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
    elif estado == "devuelto":
        q = q.filter(Prestamo.fecha_devolucion.isnot(None))
    return q.offset(skip).limit(limit).all()
