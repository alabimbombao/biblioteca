from datetime import date
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from app.models.prestamo import Prestamo
from app.models.libro import Libro
from app.models.socio import Socio
from app.schemas.prestamo import PrestamoCreate, PrestamoDevolucion
from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from typing import Optional

MULTA_POR_DIA = Decimal("0.50")
MAX_PRESTAMOS_ACTIVOS = 3


def _estado(p: Prestamo) -> str:
    hoy = date.today()
    if p.fecha_devolucion is not None:
        return "devuelto"
    if p.fecha_limite < hoy:
        return "vencido"
    return "activo"


def _enriquecer(p: Prestamo) -> Prestamo:
    p.estado = _estado(p)
    return p


def _activos_socio(db: Session, socio_id: int) -> int:
    hoy = date.today()
    return (
        db.query(func.count(Prestamo.id))
        .filter(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
        )
        .scalar()
    )


def _vencidos_socio(db: Session, socio_id: int) -> int:
    hoy = date.today()
    return (
        db.query(func.count(Prestamo.id))
        .filter(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
        .scalar()
    )


def _activos_libro(db: Session, libro_id: int) -> int:
    return (
        db.query(func.count(Prestamo.id))
        .filter(Prestamo.libro_id == libro_id, Prestamo.fecha_devolucion.is_(None))
        .scalar()
    )


def listar_prestamos(
    db: Session,
    skip: int,
    limit: int,
    estado: Optional[str] = None,
    socio_id: Optional[int] = None,
    libro_id: Optional[int] = None,
):
    hoy = date.today()
    q = db.query(Prestamo).options(
        selectinload(Prestamo.libro), selectinload(Prestamo.socio)
    )
    if socio_id:
        q = q.filter(Prestamo.socio_id == socio_id)
    if libro_id:
        q = q.filter(Prestamo.libro_id == libro_id)
    if estado == "activo":
        q = q.filter(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite >= hoy)
    elif estado == "vencido":
        q = q.filter(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
    elif estado == "devuelto":
        q = q.filter(Prestamo.fecha_devolucion.isnot(None))
    prestamos = q.offset(skip).limit(limit).all()
    for p in prestamos:
        _enriquecer(p)
    return prestamos


def obtener_prestamo(db: Session, prestamo_id: int) -> Prestamo:
    p = (
        db.query(Prestamo)
        .options(selectinload(Prestamo.libro), selectinload(Prestamo.socio))
        .filter(Prestamo.id == prestamo_id)
        .first()
    )
    if not p:
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")
    return _enriquecer(p)


def crear_prestamo(db: Session, datos: PrestamoCreate) -> Prestamo:
    hoy = date.today()

    # R1 – El socio existe
    socio = db.get(Socio, datos.socio_id)
    if not socio:
        raise NoEncontrado(f"Socio {datos.socio_id} no encontrado")

    # R2 – El libro existe
    libro = db.get(Libro, datos.libro_id)
    if not libro:
        raise NoEncontrado(f"Libro {datos.libro_id} no encontrado")

    # R3 – El socio esta activo
    if not socio.activo:
        raise ReglaNegocio("El socio no esta activo")

    # R4 – El socio no tiene prestamos vencidos
    if _vencidos_socio(db, datos.socio_id) > 0:
        raise ReglaNegocio("El socio tiene prestamos vencidos")

    # R5 – El socio no tiene mas de 3 prestamos sin devolver
    if _activos_socio(db, datos.socio_id) >= MAX_PRESTAMOS_ACTIVOS:
        raise ReglaNegocio("Maximo de 3 prestamos")

    # R6 – El socio no tiene ya ese mismo libro sin devolver
    ya_tiene = (
        db.query(Prestamo)
        .filter(
            Prestamo.socio_id == datos.socio_id,
            Prestamo.libro_id == datos.libro_id,
            Prestamo.fecha_devolucion.is_(None),
        )
        .first()
    )
    if ya_tiene:
        raise Conflicto("El socio ya tiene ese libro sin devolver")

    # R7 – El libro tiene ejemplares disponibles
    activos_libro = _activos_libro(db, datos.libro_id)
    if activos_libro >= libro.ejemplares:
        raise ReglaNegocio("No hay ejemplares disponibles")

    # R8 – Calcular fecha_limite = fecha_prestamo + dias
    fecha_prestamo = datos.fecha_prestamo or hoy
    from datetime import timedelta
    fecha_limite = fecha_prestamo + timedelta(days=datos.dias)

    prestamo = Prestamo(
        socio_id=datos.socio_id,
        libro_id=datos.libro_id,
        fecha_prestamo=fecha_prestamo,
        fecha_limite=fecha_limite,
        multa=Decimal("0"),
    )
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return obtener_prestamo(db, prestamo.id)


def devolver_prestamo(db: Session, prestamo_id: int, datos: PrestamoDevolucion) -> Prestamo:
    # R9 – El prestamo existe, no fue devuelto y la fecha no es anterior
    p = db.get(Prestamo, prestamo_id)
    if not p:
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")
    if p.fecha_devolucion is not None:
        raise Conflicto("Este prestamo ya fue devuelto")

    fecha_dev = datos.fecha_devolucion or date.today()
    if fecha_dev < p.fecha_prestamo:
        raise ReglaNegocio("La fecha de devolucion no puede ser anterior al prestamo")

    # R10 – Si se devuelve tarde: multa = dias de retraso x 0.50
    p.fecha_devolucion = fecha_dev
    if fecha_dev > p.fecha_limite:
        dias_retraso = (fecha_dev - p.fecha_limite).days
        p.multa = dias_retraso * MULTA_POR_DIA
    else:
        p.multa = Decimal("0")

    db.commit()
    return obtener_prestamo(db, prestamo_id)
