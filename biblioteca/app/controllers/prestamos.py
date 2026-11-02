"""Controlador de préstamos y multas."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from app.models.libro import Libro
from app.models.prestamo import Prestamo
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.prestamo import PrestamoCreate, PrestamoDevolucion

MULTA_POR_DIA = Decimal("0.50")
MAX_PRESTAMOS_ACTIVOS = 3


def _activos_socio(db: Session, socio_id: int) -> int:
    """Cuenta los préstamos sin devolver de un socio."""
    return db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0


def _vencidos_socio(db: Session, socio_id: int) -> int:
    """Cuenta los préstamos vencidos y sin devolver de un socio."""
    return db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < date.today(),
        )
    ) or 0


def _activos_libro(db: Session, libro_id: int) -> int:
    """Cuenta los préstamos sin devolver de un libro."""
    return db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0


def _multas_pendientes(db: Session, socio_id: int) -> int:
    """Cuenta las multas generadas que aún no se han pagado."""
    return db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.multa > 0,
            Prestamo.multa_pagada.is_(False),
        )
    ) or 0


def listar_prestamos(
    db: Session,
    usuario: Usuario,
    skip: int,
    limit: int,
    estado: str | None = None,
    socio_id: int | None = None,
    libro_id: int | None = None,
) -> tuple[list[Prestamo], int]:
    """Lista préstamos aplicando la regla de propiedad del socio."""
    hoy = date.today()
    filtros = []

    # Un socio solo puede ver sus propios préstamos, aunque envíe ?socio_id=
    if usuario.rol == RolUsuario.socio:
        filtros.append(Prestamo.socio_id == usuario.socio_id)
    elif socio_id is not None:
        filtros.append(Prestamo.socio_id == socio_id)

    if libro_id is not None:
        filtros.append(Prestamo.libro_id == libro_id)

    if estado == "activo":
        filtros.extend(
            [
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite >= hoy,
            ]
        )
    elif estado == "vencido":
        filtros.extend(
            [
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite < hoy,
            ]
        )
    elif estado == "devuelto":
        filtros.append(Prestamo.fecha_devolucion.isnot(None))

    consulta = (
        select(Prestamo)
        .options(
            selectinload(Prestamo.libro),
            selectinload(Prestamo.socio),
        )
        .where(*filtros)
    )
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    items = db.scalars(
        consulta.order_by(Prestamo.id.desc()).offset(skip).limit(limit)
    ).all()

    return list(items), total


def obtener_prestamo(
    db: Session,
    prestamo_id: int,
    usuario: Usuario | None = None,
) -> Prestamo:
    """Busca un préstamo o lanza 404.

    Si el solicitante es un socio, un préstamo ajeno responde 404 para no
    revelar que el recurso existe (regla Z2).
    """
    prestamo = db.scalar(
        select(Prestamo)
        .options(
            selectinload(Prestamo.libro),
            selectinload(Prestamo.socio),
        )
        .where(Prestamo.id == prestamo_id)
    )
    if not prestamo:
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")

    if (
        usuario is not None
        and usuario.rol == RolUsuario.socio
        and prestamo.socio_id != usuario.socio_id
    ):
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")

    return prestamo


def crear_prestamo(
    db: Session, datos: PrestamoCreate, usuario: Usuario
) -> Prestamo:
    """Registra un préstamo aplicando las reglas R1 a R11."""
    socio = db.get(Socio, datos.socio_id)
    if not socio:
        raise NoEncontrado(f"Socio {datos.socio_id} no encontrado")

    libro = db.get(Libro, datos.libro_id)
    if not libro:
        raise NoEncontrado(f"Libro {datos.libro_id} no encontrado")

    if not socio.activo:
        raise ReglaNegocio("El socio no esta activo")

    # R11: un socio con multas sin pagar no puede pedir préstamos.
    if _multas_pendientes(db, datos.socio_id) > 0:
        raise ReglaNegocio("El socio tiene multas pendientes")

    if _vencidos_socio(db, datos.socio_id) > 0:
        raise ReglaNegocio("El socio tiene prestamos vencidos")

    if _activos_socio(db, datos.socio_id) >= MAX_PRESTAMOS_ACTIVOS:
        raise ReglaNegocio("Maximo de 3 prestamos")

    ya_tiene = db.scalar(
        select(Prestamo).where(
            Prestamo.socio_id == datos.socio_id,
            Prestamo.libro_id == datos.libro_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    )
    if ya_tiene:
        raise Conflicto("El socio ya tiene ese libro sin devolver")

    if _activos_libro(db, datos.libro_id) >= libro.ejemplares:
        raise ReglaNegocio("No hay ejemplares disponibles")

    fecha_prestamo = datos.fecha_prestamo or date.today()
    fecha_limite = fecha_prestamo + timedelta(days=datos.dias)

    prestamo = Prestamo(
        socio_id=datos.socio_id,
        libro_id=datos.libro_id,
        fecha_prestamo=fecha_prestamo,
        fecha_limite=fecha_limite,
        multa=Decimal("0.00"),
        multa_pagada=True,
        registrado_por_id=usuario.id,
    )
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return obtener_prestamo(db, prestamo.id)


def devolver_prestamo(
    db: Session, prestamo_id: int, datos: PrestamoDevolucion
) -> Prestamo:
    """Registra una devolución y calcula la multa si llega tarde."""
    prestamo = db.get(Prestamo, prestamo_id)
    if not prestamo:
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")
    if prestamo.fecha_devolucion is not None:
        raise Conflicto("Este prestamo ya fue devuelto")

    fecha_devolucion = datos.fecha_devolucion or date.today()
    if fecha_devolucion < prestamo.fecha_prestamo:
        raise ReglaNegocio(
            "La fecha de devolucion no puede ser anterior al prestamo"
        )

    prestamo.fecha_devolucion = fecha_devolucion
    if fecha_devolucion > prestamo.fecha_limite:
        dias_retraso = (fecha_devolucion - prestamo.fecha_limite).days
        prestamo.multa = dias_retraso * MULTA_POR_DIA
        prestamo.multa_pagada = False
    else:
        prestamo.multa = Decimal("0.00")
        prestamo.multa_pagada = True

    db.commit()
    return obtener_prestamo(db, prestamo_id)


def pagar_multa(db: Session, prestamo_id: int) -> Prestamo:
    """Marca como pagada la multa de un préstamo."""
    prestamo = db.get(Prestamo, prestamo_id)
    if not prestamo:
        raise NoEncontrado(f"Prestamo {prestamo_id} no encontrado")

    if prestamo.multa <= 0 or prestamo.multa_pagada:
        raise Conflicto("El prestamo no tiene multa o ya fue pagada")

    prestamo.multa_pagada = True
    db.commit()
    return obtener_prestamo(db, prestamo_id)
