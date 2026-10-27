"""
generar_biblioteca.py
=====================
Genera la estructura completa del proyecto Biblioteca API REST
(FastAPI + SQLAlchemy + PostgreSQL) — 7 fases del taller.

Uso:
    python generar_biblioteca.py
"""

import os
import textwrap

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca")


def mkfile(rel_path: str, content: str = "") -> None:
    abs_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))
    print(f"  [OK] {rel_path}")


# ══════════════════════════════════════════════════════════════
# ARCHIVOS RAÍZ
# ══════════════════════════════════════════════════════════════
def crear_raiz():
    mkfile(".env.example", """\
DATABASE_URL=postgresql+psycopg2://usuario:contrasena@localhost:5432/biblioteca
""")

    mkfile(".gitignore", """\
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
""")

    mkfile("requirements.txt", """\
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic[email]
python-dotenv
""")

    mkfile("README.md", """\
# Biblioteca API REST

API REST completa para gestionar una biblioteca con FastAPI, SQLAlchemy y PostgreSQL.

## Instalación

```bash
python -m venv .venv
.venv\\Scripts\\activate          # Windows
pip install -r requirements.txt
cp .env.example .env             # Editar con tus credenciales
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

## Endpoints

| Recurso       | Rutas base         |
|---------------|--------------------|
| Autores       | /autores           |
| Categorías    | /categorias        |
| Libros        | /libros            |
| Socios        | /socios            |
| Préstamos     | /prestamos         |
| Reportes      | /reportes          |
""")


# ══════════════════════════════════════════════════════════════
# FASE 1 – INFRAESTRUCTURA
# ══════════════════════════════════════════════════════════════
def crear_core():
    mkfile("app/__init__.py", "")
    mkfile("app/core/__init__.py", "")

    mkfile("app/core/database.py", """\
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no configurada en .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
""")

    mkfile("app/core/dependencies.py", """\
from typing import Annotated, Generator
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


class Paginacion:
    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Registros a omitir"),
        limit: int = Query(default=10, ge=1, le=100, description="Max registros"),
    ):
        self.skip = skip
        self.limit = limit


PaginacionDep = Annotated[Paginacion, Depends()]
""")

    mkfile("app/core/exceptions.py", """\
class ErrorAplicacion(Exception):
    \"\"\"Clase base de todas las excepciones propias (400).\"\"\"
    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NoEncontrado(ErrorAplicacion):
    \"\"\"El recurso no existe (404).\"\"\"
    status_code = 404


class Conflicto(ErrorAplicacion):
    \"\"\"Datos duplicados o borrar algo con dependientes (409).\"\"\"
    status_code = 409


class ReglaNegocio(ErrorAplicacion):
    \"\"\"Una regla de la biblioteca no se cumple (422).\"\"\"
    status_code = 422
""")


# ══════════════════════════════════════════════════════════════
# MODELOS SQLAlchemy
# ══════════════════════════════════════════════════════════════
def crear_models():
    mkfile("app/models/__init__.py", "")

    mkfile("app/models/autor.py", """\
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Autor(Base):
    __tablename__ = "autores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    nacionalidad = Column(String(60), nullable=True)
    anio_nacimiento = Column(Integer, nullable=True)

    libros = relationship("Libro", back_populates="autor")
""")

    mkfile("app/models/libro_categoria.py", """\
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.core.database import Base

libro_categoria = Table(
    "libro_categoria",
    Base.metadata,
    Column("libro_id", Integer, ForeignKey("libros.id"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("categorias.id"), primary_key=True),
)
""")

    mkfile("app/models/categoria.py", """\
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.libro_categoria import libro_categoria


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(200), nullable=True)

    libros = relationship("Libro", secondary=libro_categoria, back_populates="categorias")
""")

    mkfile("app/models/libro.py", """\
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.libro_categoria import libro_categoria


class Libro(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    isbn = Column(String(13), unique=True, nullable=False)
    anio_publicacion = Column(Integer, nullable=False)
    ejemplares = Column(Integer, nullable=False, default=1)
    autor_id = Column(Integer, ForeignKey("autores.id"), nullable=False)

    autor = relationship("Autor", back_populates="libros")
    categorias = relationship(
        "Categoria", secondary=libro_categoria, back_populates="libros"
    )
    prestamos = relationship("Prestamo", back_populates="libro")
""")

    mkfile("app/models/socio.py", """\
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Socio(Base):
    __tablename__ = "socios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(15), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_alta = Column(DateTime, server_default=func.now(), nullable=False)

    prestamos = relationship("Prestamo", back_populates="socio")
""")

    mkfile("app/models/prestamo.py", """\
from datetime import date
from sqlalchemy import Column, Date, Numeric, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    fecha_prestamo = Column(Date, nullable=False, default=date.today)
    fecha_limite = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=True)
    multa = Column(Numeric(10, 2), nullable=False, default=0)

    socio = relationship("Socio", back_populates="prestamos")
    libro = relationship("Libro", back_populates="prestamos")
""")


# ══════════════════════════════════════════════════════════════
# SCHEMAS Pydantic
# ══════════════════════════════════════════════════════════════
def crear_schemas():
    mkfile("app/schemas/__init__.py", "")

    mkfile("app/schemas/autor.py", """\
import datetime
from pydantic import BaseModel, field_validator
from typing import Optional


class AutorBase(BaseModel):
    nombre: str
    nacionalidad: Optional[str] = None
    anio_nacimiento: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        v = " ".join(v.split()).title()
        if not (2 <= len(v) <= 100):
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return v

    @field_validator("anio_nacimiento")
    @classmethod
    def validar_anio(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1000 <= v <= datetime.date.today().year):
            raise ValueError("anio_nacimiento fuera de rango")
        return v


class AutorCreate(AutorBase):
    pass


class AutorUpdate(BaseModel):
    nombre: Optional[str] = None
    nacionalidad: Optional[str] = None
    anio_nacimiento: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).title()
        return v


class AutorOut(AutorBase):
    id: int

    model_config = {"from_attributes": True}
""")

    mkfile("app/schemas/categoria.py", """\
from pydantic import BaseModel, field_validator
from typing import Optional


class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        v = " ".join(v.split()).lower()
        if not (3 <= len(v) <= 50):
            raise ValueError("nombre debe tener entre 3 y 50 caracteres")
        return v


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).lower()
        return v


class CategoriaOut(CategoriaBase):
    id: int

    model_config = {"from_attributes": True}
""")

    mkfile("app/schemas/libro.py", """\
import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.schemas.autor import AutorOut
from app.schemas.categoria import CategoriaOut


class LibroBase(BaseModel):
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    autor_id: int

    @field_validator("titulo")
    @classmethod
    def limpiar_titulo(cls, v: str) -> str:
        v = " ".join(v.split()).title()
        if not (1 <= len(v) <= 150):
            raise ValueError("titulo debe tener entre 1 y 150 caracteres")
        return v

    @field_validator("isbn")
    @classmethod
    def validar_isbn(cls, v: str) -> str:
        if len(v) != 13 or not v.isdigit():
            raise ValueError("isbn debe tener exactamente 13 digitos")
        return v

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        if not (1450 <= v <= datetime.date.today().year):
            raise ValueError("anio_publicacion fuera de rango (1450-anio actual)")
        return v

    @field_validator("ejemplares")
    @classmethod
    def validar_ejemplares(cls, v: int) -> int:
        if not (1 <= v <= 50):
            raise ValueError("ejemplares debe estar entre 1 y 50")
        return v


class LibroCreate(LibroBase):
    categoria_ids: List[int] = Field(..., min_length=1, max_length=5)

    @field_validator("categoria_ids")
    @classmethod
    def sin_repetidos(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("categoria_ids no debe tener repetidos")
        return v


class LibroUpdate(BaseModel):
    titulo: Optional[str] = None
    anio_publicacion: Optional[int] = None
    ejemplares: Optional[int] = None
    categoria_ids: Optional[List[int]] = None


class LibroOut(BaseModel):
    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    autor: AutorOut
    categorias: List[CategoriaOut]

    model_config = {"from_attributes": True}
""")

    mkfile("app/schemas/socio.py", """\
import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class SocioBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        return " ".join(v.split()).title()

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not (7 <= len(v) <= 15):
                raise ValueError("telefono debe tener entre 7 y 15 caracteres")
            if not re.match(r"^[\\d\\s+]+$", v):
                raise ValueError("telefono solo puede contener digitos, espacios o +")
        return v


class SocioCreate(SocioBase):
    pass


class SocioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.split()).title()
        return v


class SocioOut(SocioBase):
    id: int
    activo: bool
    fecha_alta: datetime

    model_config = {"from_attributes": True}
""")

    mkfile("app/schemas/prestamo.py", """\
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, field_validator
from typing import Optional
from app.schemas.libro import LibroOut
from app.schemas.socio import SocioOut


class PrestamoCreate(BaseModel):
    socio_id: int
    libro_id: int
    fecha_prestamo: Optional[date] = None
    dias: int = 14

    @field_validator("dias")
    @classmethod
    def validar_dias(cls, v: int) -> int:
        if not (1 <= v <= 30):
            raise ValueError("dias debe estar entre 1 y 30")
        return v


class PrestamoDevolucion(BaseModel):
    fecha_devolucion: Optional[date] = None


class PrestamoOut(BaseModel):
    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: Optional[date] = None
    multa: Decimal
    estado: str
    socio: Optional[SocioOut] = None
    libro: Optional[LibroOut] = None

    model_config = {"from_attributes": True}
""")

    mkfile("app/schemas/reportes.py", """\
from pydantic import BaseModel
from typing import Optional


class LibroMasPrestado(BaseModel):
    libro_id: int
    titulo: str
    autor: str
    total_prestamos: int

    model_config = {"from_attributes": True}


class CategoriaTotalLibros(BaseModel):
    categoria_id: int
    nombre: str
    total_libros: int

    model_config = {"from_attributes": True}


class PrestamoVencido(BaseModel):
    prestamo_id: int
    titulo: str
    socio: str
    email: str
    fecha_limite: str
    dias_retraso: int

    model_config = {"from_attributes": True}


class SocioConMulta(BaseModel):
    socio_id: int
    nombre: str
    total_multas: float
    total_prestamos: int

    model_config = {"from_attributes": True}


class AutorReporte(BaseModel):
    autor_id: int
    nombre: str
    total_libros: int
    total_ejemplares: int
    total_prestamos: int

    model_config = {"from_attributes": True}


class ResumenBiblioteca(BaseModel):
    total_libros: int
    total_ejemplares: int
    total_prestados: int
    total_socios_activos: int
    total_socios_vencidos: int
    total_multas: float

    model_config = {"from_attributes": True}
""")


# ══════════════════════════════════════════════════════════════
# CONTROLLERS
# ══════════════════════════════════════════════════════════════
def crear_controllers():
    mkfile("app/controllers/__init__.py", "")

    # ── autores.py ────────────────────────────────────────────
    mkfile("app/controllers/autores.py", """\
from sqlalchemy.orm import Session
from app.models.autor import Autor
from app.schemas.autor import AutorCreate, AutorUpdate
from app.core.exceptions import Conflicto, NoEncontrado
from typing import Optional


def listar_autores(db: Session, skip: int, limit: int, nacionalidad: Optional[str]):
    q = db.query(Autor)
    if nacionalidad:
        q = q.filter(Autor.nacionalidad.ilike(f"%{nacionalidad}%"))
    return q.offset(skip).limit(limit).all()


def obtener_autor(db: Session, autor_id: int) -> Autor:
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado(f"Autor {autor_id} no encontrado")
    return autor


def crear_autor(db: Session, datos: AutorCreate) -> Autor:
    if db.query(Autor).filter(Autor.nombre == datos.nombre).first():
        raise Conflicto(f"Ya existe un autor con nombre '{datos.nombre}'")
    autor = Autor(**datos.model_dump())
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor


def actualizar_autor(db: Session, autor_id: int, datos: AutorUpdate) -> Autor:
    autor = obtener_autor(db, autor_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != autor.nombre:
        if db.query(Autor).filter(Autor.nombre == cambios["nombre"]).first():
            raise Conflicto(f"Ya existe un autor con nombre '{cambios['nombre']}'")
    for k, v in cambios.items():
        setattr(autor, k, v)
    db.commit()
    db.refresh(autor)
    return autor


def eliminar_autor(db: Session, autor_id: int) -> None:
    autor = obtener_autor(db, autor_id)
    if autor.libros:
        raise Conflicto("No se puede eliminar: el autor tiene libros registrados")
    db.delete(autor)
    db.commit()
""")

    # ── categorias.py ─────────────────────────────────────────
    mkfile("app/controllers/categorias.py", """\
from sqlalchemy.orm import Session
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.core.exceptions import Conflicto, NoEncontrado


def listar_categorias(db: Session, skip: int, limit: int):
    return db.query(Categoria).offset(skip).limit(limit).all()


def obtener_categoria(db: Session, categoria_id: int) -> Categoria:
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise NoEncontrado(f"Categoria {categoria_id} no encontrada")
    return cat


def crear_categoria(db: Session, datos: CategoriaCreate) -> Categoria:
    if db.query(Categoria).filter(Categoria.nombre == datos.nombre).first():
        raise Conflicto(f"Ya existe la categoria '{datos.nombre}'")
    cat = Categoria(**datos.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def actualizar_categoria(db: Session, categoria_id: int, datos: CategoriaUpdate) -> Categoria:
    cat = obtener_categoria(db, categoria_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != cat.nombre:
        if db.query(Categoria).filter(Categoria.nombre == cambios["nombre"]).first():
            raise Conflicto(f"Ya existe la categoria '{cambios['nombre']}'")
    for k, v in cambios.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def eliminar_categoria(db: Session, categoria_id: int) -> None:
    cat = obtener_categoria(db, categoria_id)
    # Quitar de todos los libros (relacion M:N)
    cat.libros.clear()
    db.delete(cat)
    db.commit()
""")

    # ── libros.py ─────────────────────────────────────────────
    mkfile("app/controllers/libros.py", """\
from enum import Enum
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.prestamo import Prestamo
from app.schemas.libro import LibroCreate, LibroUpdate
from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from typing import Optional


class OrdenLibro(str, Enum):
    titulo = "titulo"
    anio = "anio"


def _activos_libro(db: Session, libro_id: int) -> int:
    return (
        db.query(func.count(Prestamo.id))
        .filter(Prestamo.libro_id == libro_id, Prestamo.fecha_devolucion.is_(None))
        .scalar()
    )


def _enriquecer(libro: Libro, db: Session) -> Libro:
    libro.disponibles = libro.ejemplares - _activos_libro(db, libro.id)
    return libro


def listar_libros(
    db: Session,
    skip: int,
    limit: int,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibro] = None,
):
    q = db.query(Libro).options(selectinload(Libro.autor), selectinload(Libro.categorias))
    if buscar:
        q = q.filter(Libro.titulo.ilike(f"%{buscar}%"))
    if autor:
        q = q.join(Libro.autor).filter(Autor.nombre.ilike(f"%{autor}%"))
    if categoria_id:
        q = q.join(Libro.categorias).filter(Categoria.id == categoria_id)
    if desde:
        q = q.filter(Libro.anio_publicacion >= desde)
    if hasta:
        q = q.filter(Libro.anio_publicacion <= hasta)
    if orden == OrdenLibro.anio:
        q = q.order_by(Libro.anio_publicacion.desc())
    else:
        q = q.order_by(Libro.titulo)
    libros = q.offset(skip).limit(limit).all()
    for l in libros:
        _enriquecer(l, db)
    return libros


def obtener_libro(db: Session, libro_id: int) -> Libro:
    libro = (
        db.query(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .filter(Libro.id == libro_id)
        .first()
    )
    if not libro:
        raise NoEncontrado(f"Libro {libro_id} no encontrado")
    return _enriquecer(libro, db)


def crear_libro(db: Session, datos: LibroCreate) -> Libro:
    if not db.get(Autor, datos.autor_id):
        raise NoEncontrado(f"Autor {datos.autor_id} no encontrado")
    if db.query(Libro).filter(Libro.isbn == datos.isbn).first():
        raise Conflicto(f"Ya existe un libro con ISBN '{datos.isbn}'")
    categorias = []
    for cid in datos.categoria_ids:
        cat = db.get(Categoria, cid)
        if not cat:
            raise NoEncontrado(f"Categoria {cid} no encontrada")
        categorias.append(cat)
    libro_data = datos.model_dump(exclude={"categoria_ids"})
    libro = Libro(**libro_data)
    libro.categorias = categorias
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return obtener_libro(db, libro.id)


def actualizar_libro(db: Session, libro_id: int, datos: LibroUpdate) -> Libro:
    libro = obtener_libro(db, libro_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "categoria_ids" in cambios:
        categorias = []
        for cid in cambios.pop("categoria_ids"):
            cat = db.get(Categoria, cid)
            if not cat:
                raise NoEncontrado(f"Categoria {cid} no encontrada")
            categorias.append(cat)
        libro.categorias = categorias
    if "ejemplares" in cambios:
        activos = _activos_libro(db, libro_id)
        if cambios["ejemplares"] < activos:
            raise ReglaNegocio(
                f"No se puede reducir ejemplares: hay {activos} prestamos activos"
            )
    for k, v in cambios.items():
        setattr(libro, k, v)
    db.commit()
    return obtener_libro(db, libro_id)


def eliminar_libro(db: Session, libro_id: int) -> None:
    libro = obtener_libro(db, libro_id)
    activos = _activos_libro(db, libro_id)
    if activos:
        raise Conflicto("No se puede eliminar: el libro tiene prestamos sin devolver")
    db.delete(libro)
    db.commit()


def libros_de_autor(db: Session, autor_id: int, skip: int, limit: int):
    if not db.get(Autor, autor_id):
        raise NoEncontrado(f"Autor {autor_id} no encontrado")
    libros = (
        db.query(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .filter(Libro.autor_id == autor_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    for l in libros:
        _enriquecer(l, db)
    return libros
""")

    # ── socios.py ─────────────────────────────────────────────
    mkfile("app/controllers/socios.py", """\
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
""")

    # ── prestamos.py ──────────────────────────────────────────
    mkfile("app/controllers/prestamos.py", """\
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
""")

    # ── reportes.py ───────────────────────────────────────────
    mkfile("app/controllers/reportes.py", """\
from datetime import date
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from app.models.prestamo import Prestamo
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.socio import Socio
from app.models.categoria import Categoria
from app.models.libro_categoria import libro_categoria


def libros_mas_prestados(db: Session, limite: int = 5):
    \"\"\"Libro, autor y total de prestamos, de mayor a menor (join + group_by + count + order_by).\"\"\"
    rows = (
        db.query(
            Prestamo.libro_id,
            Libro.titulo,
            Autor.nombre.label("autor"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Autor, Libro.autor_id == Autor.id)
        .group_by(Prestamo.libro_id, Libro.titulo, Autor.nombre)
        .order_by(func.count(Prestamo.id).desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "libro_id": r.libro_id,
            "titulo": r.titulo,
            "autor": r.autor,
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def categorias_total_libros(db: Session):
    \"\"\"Total de libros por categoria, incluidas las que tienen 0 (outerjoin + group_by).\"\"\"
    total = func.count(libro_categoria.c.libro_id).label("total_libros")
    rows = (
        db.query(Categoria.id.label("categoria_id"), Categoria.nombre, total)
        .outerjoin(libro_categoria, libro_categoria.c.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nombre)
        .all()
    )
    return [
        {"categoria_id": r.categoria_id, "nombre": r.nombre, "total_libros": r.total_libros}
        for r in rows
    ]


def prestamos_vencidos(db: Session):
    \"\"\"Prestamos vencidos con titulo, socio, email, fecha_limite y dias de retraso
    (join de 3 tablas + where).\"\"\"
    hoy = date.today()
    rows = (
        db.query(
            Prestamo.id.label("prestamo_id"),
            Libro.titulo,
            Socio.nombre.label("socio"),
            Socio.email,
            Prestamo.fecha_limite,
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Socio, Prestamo.socio_id == Socio.id)
        .filter(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
        .all()
    )
    return [
        {
            "prestamo_id": r.prestamo_id,
            "titulo": r.titulo,
            "socio": r.socio,
            "email": r.email,
            "fecha_limite": str(r.fecha_limite),
            "dias_retraso": (hoy - r.fecha_limite).days,
        }
        for r in rows
    ]


def socios_con_multas(db: Session):
    \"\"\"Socio, total de multas y total de prestamos con multa (group_by + sum + having).\"\"\"
    rows = (
        db.query(
            Prestamo.socio_id,
            Socio.nombre,
            func.sum(Prestamo.multa).label("total_multas"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Socio, Prestamo.socio_id == Socio.id)
        .filter(Prestamo.multa > 0)
        .group_by(Prestamo.socio_id, Socio.nombre)
        .having(func.sum(Prestamo.multa) > 0)
        .order_by(func.sum(Prestamo.multa).desc())
        .all()
    )
    return [
        {
            "socio_id": r.socio_id,
            "nombre": r.nombre,
            "total_multas": float(r.total_multas),
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def reporte_autores(db: Session):
    \"\"\"Libros, ejemplares y prestamos de cada autor (outerjoin + count(distinct)).\"\"\"
    rows = (
        db.query(
            Autor.id.label("autor_id"),
            Autor.nombre,
            func.count(distinct(Libro.id)).label("total_libros"),
            func.coalesce(func.sum(Libro.ejemplares), 0).label("total_ejemplares"),
            func.count(distinct(Prestamo.id)).label("total_prestamos"),
        )
        .outerjoin(Libro, Libro.autor_id == Autor.id)
        .outerjoin(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Autor.id, Autor.nombre)
        .all()
    )
    return [
        {
            "autor_id": r.autor_id,
            "nombre": r.nombre,
            "total_libros": r.total_libros,
            "total_ejemplares": r.total_ejemplares,
            "total_prestamos": r.total_prestamos,
        }
        for r in rows
    ]


def resumen_biblioteca(db: Session):
    \"\"\"Totales: libros, ejemplares, prestados, socios activos, vencidos y multas
    (select(func.count()) + func.sum).\"\"\"
    hoy = date.today()
    total_libros = db.query(func.count(Libro.id)).scalar()
    total_ejemplares = db.query(func.coalesce(func.sum(Libro.ejemplares), 0)).scalar()
    total_prestados = (
        db.query(func.count(Prestamo.id))
        .filter(Prestamo.fecha_devolucion.is_(None))
        .scalar()
    )
    total_socios_activos = (
        db.query(func.count(Socio.id)).filter(Socio.activo.is_(True)).scalar()
    )
    total_socios_vencidos = (
        db.query(func.count(distinct(Prestamo.socio_id)))
        .filter(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
        .scalar()
    )
    total_multas = db.query(func.coalesce(func.sum(Prestamo.multa), 0)).scalar()
    return {
        "total_libros": total_libros,
        "total_ejemplares": int(total_ejemplares),
        "total_prestados": total_prestados,
        "total_socios_activos": total_socios_activos,
        "total_socios_vencidos": total_socios_vencidos,
        "total_multas": float(total_multas),
    }
""")


# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════
def crear_routes():
    mkfile("app/routes/__init__.py", "")

    mkfile("app/routes/autores.py", """\
from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.autor import AutorCreate, AutorUpdate, AutorOut
import app.controllers.autores as ctrl

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get("/", response_model=List[AutorOut])
def listar(pag: PaginacionDep, db: SessionDep, nacionalidad: Optional[str] = None):
    return ctrl.listar_autores(db, pag.skip, pag.limit, nacionalidad)


@router.get("/{autor_id}", response_model=AutorOut)
def obtener(autor_id: int, db: SessionDep):
    return ctrl.obtener_autor(db, autor_id)


@router.post("/", response_model=AutorOut, status_code=201)
def crear(datos: AutorCreate, db: SessionDep):
    return ctrl.crear_autor(db, datos)


@router.patch("/{autor_id}", response_model=AutorOut)
def actualizar(autor_id: int, datos: AutorUpdate, db: SessionDep):
    return ctrl.actualizar_autor(db, autor_id, datos)


@router.delete("/{autor_id}", status_code=204)
def eliminar(autor_id: int, db: SessionDep):
    ctrl.eliminar_autor(db, autor_id)
""")

    mkfile("app/routes/categorias.py", """\
from fastapi import APIRouter
from typing import List
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaOut
import app.controllers.categorias as ctrl

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/", response_model=List[CategoriaOut])
def listar(pag: PaginacionDep, db: SessionDep):
    return ctrl.listar_categorias(db, pag.skip, pag.limit)


@router.post("/", response_model=CategoriaOut, status_code=201)
def crear(datos: CategoriaCreate, db: SessionDep):
    return ctrl.crear_categoria(db, datos)


@router.patch("/{categoria_id}", response_model=CategoriaOut)
def actualizar(categoria_id: int, datos: CategoriaUpdate, db: SessionDep):
    return ctrl.actualizar_categoria(db, categoria_id, datos)


@router.delete("/{categoria_id}", status_code=204)
def eliminar(categoria_id: int, db: SessionDep):
    ctrl.eliminar_categoria(db, categoria_id)
""")

    mkfile("app/routes/libros.py", """\
from fastapi import APIRouter
from typing import List, Optional
from app.core.dependencies import SessionDep, PaginacionDep
from app.schemas.libro import LibroCreate, LibroUpdate, LibroOut
from app.controllers.libros import OrdenLibro
import app.controllers.libros as ctrl

router = APIRouter(tags=["Libros"])


@router.get("/libros", response_model=List[LibroOut])
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibro] = None,
):
    return ctrl.listar_libros(
        db, pag.skip, pag.limit, buscar, autor, categoria_id, desde, hasta, orden
    )


@router.get("/libros/{libro_id}", response_model=LibroOut)
def obtener(libro_id: int, db: SessionDep):
    return ctrl.obtener_libro(db, libro_id)


@router.post("/libros", response_model=LibroOut, status_code=201)
def crear(datos: LibroCreate, db: SessionDep):
    return ctrl.crear_libro(db, datos)


@router.patch("/libros/{libro_id}", response_model=LibroOut)
def actualizar(libro_id: int, datos: LibroUpdate, db: SessionDep):
    return ctrl.actualizar_libro(db, libro_id, datos)


@router.delete("/libros/{libro_id}", status_code=204)
def eliminar(libro_id: int, db: SessionDep):
    ctrl.eliminar_libro(db, libro_id)


@router.get("/autores/{autor_id}/libros", response_model=List[LibroOut], tags=["Autores"])
def libros_de_autor(autor_id: int, pag: PaginacionDep, db: SessionDep):
    return ctrl.libros_de_autor(db, autor_id, pag.skip, pag.limit)
""")

    mkfile("app/routes/socios.py", """\
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
""")

    mkfile("app/routes/prestamos.py", """\
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
""")

    mkfile("app/routes/reportes.py", """\
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
""")


# ══════════════════════════════════════════════════════════════
# main.py
# ══════════════════════════════════════════════════════════════
def crear_main():
    mkfile("app/main.py", """\
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.database import Base, engine
from app.core.exceptions import ErrorAplicacion

# Registrar modelos antes de create_all
import app.models.autor            # noqa: F401
import app.models.categoria        # noqa: F401
import app.models.libro_categoria  # noqa: F401
import app.models.libro            # noqa: F401
import app.models.socio            # noqa: F401
import app.models.prestamo         # noqa: F401

from app.routes import autores, categorias, libros, socios, prestamos, reportes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Biblioteca API REST",
    description="API REST completa para gestionar una biblioteca (7 fases).",
    version="1.0.0",
)


@app.exception_handler(ErrorAplicacion)
async def exception_handler(request: Request, exc: ErrorAplicacion):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(autores.router)
app.include_router(categorias.router)
app.include_router(libros.router)
app.include_router(socios.router)
app.include_router(prestamos.router)
app.include_router(reportes.router)
""")


# ══════════════════════════════════════════════════════════════
# FASE 7 – Script de datos de prueba (seeder)
# ══════════════════════════════════════════════════════════════
def crear_seeder():
    mkfile("seeder.py", """\
\"\"\"
seeder.py – Carga los datos de prueba de la Fase 7.
Ejecutar con la API en marcha O directamente contra la BD:

    python seeder.py
\"\"\"

import requests
from datetime import date, timedelta

BASE = "http://127.0.0.1:8000"


def post(ruta, datos):
    r = requests.post(f"{BASE}{ruta}", json=datos)
    print(f"  POST {ruta} → {r.status_code}")
    if r.status_code not in (200, 201):
        print("   ", r.json())
        return None
    return r.json()


def patch(ruta, datos):
    r = requests.patch(f"{BASE}{ruta}", json=datos)
    print(f"  PATCH {ruta} → {r.status_code}")
    if r.status_code not in (200, 201):
        print("   ", r.json())
    return r.json() if r.ok else None


def get(ruta, params=None):
    r = requests.get(f"{BASE}{ruta}", params=params)
    print(f"  GET {ruta} → {r.status_code}")
    return r.json() if r.ok else None


# ── Autores ──────────────────────────────────────────────────
print("\\n=== Autores ===")
a1 = post("/autores", {"nombre": "Gabriel Garcia Marquez", "nacionalidad": "Colombiana", "anio_nacimiento": 1927})
a2 = post("/autores", {"nombre": "Isabel Allende", "nacionalidad": "Chilena", "anio_nacimiento": 1942})
a3 = post("/autores", {"nombre": "George Orwell", "nacionalidad": "Britanica", "anio_nacimiento": 1903})

# ── Categorias ───────────────────────────────────────────────
print("\\n=== Categorias ===")
c1 = post("/categorias", {"nombre": "Novela"})
c2 = post("/categorias", {"nombre": "Realismo Magico"})
c3 = post("/categorias", {"nombre": "Distopia"})
c4 = post("/categorias", {"nombre": "Poesia"})

# ── Libros ───────────────────────────────────────────────────
print("\\n=== Libros ===")
l1 = post("/libros", {
    "titulo": "Cien Anos de Soledad",
    "isbn": "9780307474728",
    "anio_publicacion": 1967,
    "ejemplares": 2,
    "autor_id": a1["id"],
    "categoria_ids": [c1["id"], c2["id"]],
})
l2 = post("/libros", {
    "titulo": "El Amor en los Tiempos del Colera",
    "isbn": "9780307389732",
    "anio_publicacion": 1985,
    "ejemplares": 1,
    "autor_id": a1["id"],
    "categoria_ids": [c1["id"]],
})
l3 = post("/libros", {
    "titulo": "La Casa de los Espiritus",
    "isbn": "9781416523932",
    "anio_publicacion": 1982,
    "ejemplares": 2,
    "autor_id": a2["id"],
    "categoria_ids": [c1["id"], c2["id"]],
})
l4 = post("/libros", {
    "titulo": "1984",
    "isbn": "9780451524935",
    "anio_publicacion": 1949,
    "ejemplares": 3,
    "autor_id": a3["id"],
    "categoria_ids": [c1["id"], c3["id"]],
})

# ── Socios ───────────────────────────────────────────────────
print("\\n=== Socios ===")
s1 = post("/socios", {"nombre": "Ana Torres", "email": "ANA@example.com"})
s2 = post("/socios", {"nombre": "Luis Perez", "email": "luis@example.com"})
s3 = post("/socios", {"nombre": "Marta Ruiz", "email": "marta@example.com"})

print("\\n=== Datos de prueba cargados. ===")
print("Ahora ejecuta los 24 casos desde /docs o Postman.")
""")


# ══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\nGenerando estructura completa (7 fases) - Biblioteca API REST...\n")

    print("[Raiz]")
    crear_raiz()
    print("\n[FASE 1] Core / Infraestructura:")
    crear_core()
    print("\n[FASE 2-4] Modelos SQLAlchemy:")
    crear_models()
    print("\n[Schemas Pydantic]:")
    crear_schemas()
    print("\n[Controllers]:")
    crear_controllers()
    print("\n[Routes]:")
    crear_routes()
    print("\n[main.py]:")
    crear_main()
    print("\n[FASE 7] Seeder de prueba:")
    crear_seeder()

    print("""
----------------------------------------------------------
  PROYECTO GENERADO EN: biblioteca/
----------------------------------------------------------
  Pasos siguientes:
  1. cd biblioteca
  2. python -m venv .venv
  3. .venv\\Scripts\\activate
  4. pip install -r requirements.txt
  5. Copiar .env.example a .env y editar credenciales
  6. uvicorn app.main:app --reload
  7. Abrir http://127.0.0.1:8000/docs
  8. (opcional) python seeder.py  para datos de prueba
----------------------------------------------------------
""")
