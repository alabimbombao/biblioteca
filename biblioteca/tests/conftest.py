"""Configuración común de las pruebas con pytest."""

import os
from datetime import timedelta

# Las variables se definen antes de importar la aplicación para que
# pydantic-settings las lea al construir la configuración.
os.environ.setdefault(
    "SECRET_KEY", "clave-de-pruebas-con-mas-de-32-caracteres-123456"
)
os.environ.setdefault("DATABASE_URL", "sqlite:///./biblioteca_local_pruebas.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.dependencies import get_db  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.core.security import crear_token, hashear_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.autor import Autor  # noqa: E402
from app.models.categoria import Categoria  # noqa: E402
from app.models.libro import Libro  # noqa: E402
from app.models.socio import Socio  # noqa: E402
from app.models.usuario import RolUsuario, Usuario  # noqa: E402

URL_PRUEBAS = get_settings().test_database_url

if URL_PRUEBAS.startswith("sqlite"):
    motor = create_engine(
        URL_PRUEBAS,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    motor = create_engine(URL_PRUEBAS, pool_pre_ping=True)

FabricaSesiones = sessionmaker(
    bind=motor,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def reiniciar_limitador():
    """Reinicia el contador de slowapi antes de cada prueba."""
    limiter.reset()
    yield


@pytest.fixture()
def db():
    """Crea un esquema limpio y entrega una sesión para preparar datos."""
    Base.metadata.drop_all(bind=motor)
    Base.metadata.create_all(bind=motor)
    sesion = FabricaSesiones()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture()
def cliente(db):
    """Cliente HTTP de pruebas apuntando a la base de datos de pruebas."""

    def obtener_db_pruebas():
        sesion = FabricaSesiones()
        try:
            yield sesion
        finally:
            sesion.close()

    app.dependency_overrides[get_db] = obtener_db_pruebas
    with TestClient(app) as cliente_pruebas:
        yield cliente_pruebas
    app.dependency_overrides.clear()


def crear_socio(
    db,
    nombre: str = "Ana Torres",
    email: str = "ana@example.com",
    telefono: str | None = None,
    activo: bool = True,
) -> Socio:
    """Crea un socio de apoyo para las pruebas."""
    socio = Socio(
        nombre=nombre,
        email=email,
        telefono=telefono,
        activo=activo,
    )
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def crear_usuario(
    db,
    email: str,
    password: str,
    rol: RolUsuario,
    nombre: str = "Usuario Prueba",
    socio: Socio | None = None,
    activo: bool = True,
) -> Usuario:
    """Crea un usuario con contraseña hasheada."""
    usuario = Usuario(
        email=email.lower(),
        nombre=nombre,
        password_hash=hashear_password(password),
        rol=rol,
        activo=activo,
        socio_id=socio.id if socio else None,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def crear_socio_con_usuario(
    db,
    nombre: str,
    email: str,
    password: str,
    telefono: str | None = None,
) -> tuple[Socio, Usuario]:
    """Crea un socio y su usuario vinculado."""
    socio = crear_socio(db, nombre, email, telefono)
    usuario = crear_usuario(
        db, email, password, RolUsuario.socio, nombre, socio
    )
    return socio, usuario


def token_de(usuario: Usuario, tipo: str = "access") -> str:
    """Genera un token válido sin pasar por el endpoint de login."""
    duracion = (
        timedelta(minutes=15)
        if tipo == "access"
        else timedelta(days=7)
    )
    token, _ = crear_token(usuario, tipo, duracion)
    return token


def cabecera(usuario: Usuario, tipo: str = "access") -> dict:
    """Cabecera Authorization para un usuario."""
    return {"Authorization": f"Bearer {token_de(usuario, tipo)}"}


def crear_catalogo(db) -> tuple[Autor, Categoria, Libro]:
    """Crea un autor, una categoría y un libro de apoyo."""
    autor = Autor(
        nombre="Gabriel Garcia Marquez",
        nacionalidad="Colombiana",
        anio_nacimiento=1927,
    )
    categoria = Categoria(nombre="novela", descripcion="Novela literaria")
    db.add_all([autor, categoria])
    db.commit()
    db.refresh(autor)
    db.refresh(categoria)

    libro = Libro(
        titulo="Cien Anos De Soledad",
        isbn="9780307350435",
        anio_publicacion=1967,
        ejemplares=2,
        autor_id=autor.id,
    )
    libro.categorias = [categoria]
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return autor, categoria, libro


@pytest.fixture()
def admin(db) -> Usuario:
    """Usuario administrador de las pruebas."""
    return crear_usuario(
        db,
        "admin@biblioteca.com",
        "Admin1234",
        RolUsuario.admin,
        "Admin Sistema",
    )


@pytest.fixture()
def bibliotecario(db) -> Usuario:
    """Usuario bibliotecario de las pruebas."""
    return crear_usuario(
        db,
        "biblio@biblioteca.com",
        "Biblio1234",
        RolUsuario.bibliotecario,
        "Biblio Uno",
    )


@pytest.fixture()
def ana(db) -> Usuario:
    """Socia Ana Torres."""
    _, usuario = crear_socio_con_usuario(
        db, "Ana Torres", "ana@example.com", "Ana12345"
    )
    return usuario


@pytest.fixture()
def luis(db) -> Usuario:
    """Socio Luis Pérez."""
    _, usuario = crear_socio_con_usuario(
        db, "Luis Perez", "luis@example.com", "Luis12345"
    )
    return usuario


@pytest.fixture()
def catalogo(db):
    """Autor, categoría y libro de apoyo."""
    return crear_catalogo(db)
