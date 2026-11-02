"""Controlador de socios."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import Conflicto, NoEncontrado
from app.models.prestamo import Prestamo
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.schemas.socio import (
    SocioActualizarPropio,
    SocioCreate,
    SocioUpdate,
)


def listar_socios(
    db: Session, skip: int, limit: int, activo: bool | None
) -> tuple[list[Socio], int]:
    """Devuelve una página de socios y el total."""
    filtros = []
    if activo is not None:
        filtros.append(Socio.activo == activo)

    consulta = select(Socio).where(*filtros)
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())
    ) or 0
    items = db.scalars(
        consulta.order_by(Socio.nombre).offset(skip).limit(limit)
    ).all()
    return list(items), total


def obtener_socio(db: Session, socio_id: int) -> Socio:
    """Busca un socio o lanza 404."""
    socio = db.get(Socio, socio_id)
    if not socio:
        raise NoEncontrado(f"Socio {socio_id} no encontrado")
    return socio


def socio_del_usuario(usuario: Usuario) -> Socio:
    """Devuelve el socio vinculado al usuario autenticado."""
    if usuario.socio is None:
        raise NoEncontrado("El usuario no tiene un socio vinculado")
    return usuario.socio


def crear_socio(db: Session, datos: SocioCreate) -> Socio:
    """Crea un socio validando que el correo no exista."""
    existe = db.scalar(select(Socio).where(Socio.email == datos.email))
    if existe:
        raise Conflicto(f"Ya existe un socio con email '{datos.email}'")

    socio = Socio(**datos.model_dump())
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def actualizar_socio(
    db: Session, socio_id: int, datos: SocioUpdate
) -> Socio:
    """Actualiza los campos enviados de un socio."""
    socio = obtener_socio(db, socio_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "email" in cambios and cambios["email"] != socio.email:
        existe = db.scalar(
            select(Socio).where(Socio.email == cambios["email"])
        )
        if existe:
            raise Conflicto(f"Ya existe un socio con email '{cambios['email']}'")

    for campo, valor in cambios.items():
        setattr(socio, campo, valor)

    db.commit()
    db.refresh(socio)
    return socio


def actualizar_perfil_propio(
    db: Session, usuario: Usuario, datos: SocioActualizarPropio
) -> Socio:
    """Un socio actualiza únicamente su nombre y su teléfono."""
    socio = socio_del_usuario(usuario)
    cambios = datos.model_dump(exclude_unset=True)

    for campo, valor in cambios.items():
        setattr(socio, campo, valor)

    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio(db: Session, socio_id: int) -> None:
    """Elimina un socio sin historial o lo desactiva si lo tiene."""
    socio = obtener_socio(db, socio_id)
    tiene_historial = db.scalar(
        select(Prestamo.id).where(Prestamo.socio_id == socio_id).limit(1)
    )

    if tiene_historial or socio.usuario is not None:
        # Borrado lógico: se conserva el historial y se bloquea el acceso.
        socio.activo = False
        if socio.usuario is not None:
            socio.usuario.activo = False
        db.commit()
    else:
        db.delete(socio)
        db.commit()


def _listar_prestamos_socio(
    db: Session,
    socio_id: int,
    skip: int,
    limit: int,
    estado: str | None,
) -> tuple[list[Prestamo], int]:
    """Lista los préstamos de un socio con filtro por estado."""
    hoy = date.today()
    filtros = [Prestamo.socio_id == socio_id]

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


def prestamos_de_socio(
    db: Session,
    socio_id: int,
    skip: int,
    limit: int,
    estado: str | None,
) -> tuple[list[Prestamo], int]:
    """Préstamos de un socio consultados por el staff."""
    obtener_socio(db, socio_id)
    return _listar_prestamos_socio(db, socio_id, skip, limit, estado)


def prestamos_propios(
    db: Session,
    usuario: Usuario,
    skip: int,
    limit: int,
    estado: str | None,
) -> tuple[list[Prestamo], int]:
    """Préstamos del socio autenticado."""
    socio = socio_del_usuario(usuario)
    return _listar_prestamos_socio(db, socio.id, skip, limit, estado)


def multas_propias(
    db: Session, usuario: Usuario
) -> tuple[list[Prestamo], Decimal]:
    """Multas sin pagar del socio autenticado y su total."""
    socio = socio_del_usuario(usuario)
    filtros = [
        Prestamo.socio_id == socio.id,
        Prestamo.multa > 0,
        Prestamo.multa_pagada.is_(False),
    ]

    items = db.scalars(
        select(Prestamo)
        .options(
            selectinload(Prestamo.libro),
            selectinload(Prestamo.socio),
        )
        .where(*filtros)
        .order_by(Prestamo.id.desc())
    ).all()

    total = db.scalar(
        select(func.coalesce(func.sum(Prestamo.multa), 0)).where(*filtros)
    )
    total_adeudado = Decimal(str(total)) if total is not None else Decimal("0")

    return list(items), total_adeudado
