"""Punto de entrada de la API de la biblioteca.

Incluye routers, middlewares y manejadores de errores. La base de datos
se crea y modifica únicamente con las migraciones de Alembic.
"""

import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.exceptions import ErrorAplicacion
from app.core.rate_limit import limiter
from app.routes import (
    auth,
    autores,
    categorias,
    health,
    libros,
    prestamos,
    reportes,
    socios,
    usuario,
)

configuracion = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
registro = logging.getLogger("biblioteca")

if configuracion.es_produccion and "*" in configuracion.cors_origins:
    raise ValueError(
        "En producción no se permite el origen '*' en CORS_ORIGINS"
    )

app = FastAPI(
    title="Biblioteca API REST segura",
    description=(
        "API de la biblioteca con autenticación JWT, autorización por "
        "roles y por propiedad, y migraciones versionadas con Alembic."
    ),
    version="2.0.0",
    docs_url=None if configuracion.es_produccion else "/docs",
    redoc_url=None if configuracion.es_produccion else "/redoc",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def agregar_request_id(request: Request, call_next):
    """Genera un identificador por petición y registra su duración."""
    request_id = str(uuid4())
    inicio = time.perf_counter()

    respuesta = await call_next(request)

    duracion_ms = (time.perf_counter() - inicio) * 1000
    respuesta.headers["X-Request-ID"] = request_id
    registro.info(
        "%s %s -> %s (%.2f ms) [%s]",
        request.method,
        request.url.path,
        respuesta.status_code,
        duracion_ms,
        request_id,
    )
    return respuesta


@app.exception_handler(ErrorAplicacion)
async def manejar_error_aplicacion(request: Request, exc: ErrorAplicacion):
    """Convierte las excepciones propias en respuestas JSON."""
    cabeceras = (
        {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=cabeceras,
    )


@app.exception_handler(RateLimitExceeded)
async def manejar_limite_peticiones(request: Request, exc: RateLimitExceeded):
    """Responde 429 cuando se supera el límite de peticiones."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas peticiones. Intente de nuevo más tarde."},
    )


@app.exception_handler(Exception)
async def manejar_error_no_controlado(request: Request, exc: Exception):
    """Registra el error y responde sin mostrar el stacktrace."""
    registro.exception(
        "Error no controlado en %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


# Routers de la API REST
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(autores.router, prefix="/api/v1")
app.include_router(categorias.router, prefix="/api/v1")
app.include_router(libros.router, prefix="/api/v1")
app.include_router(socios.router, prefix="/api/v1")
app.include_router(prestamos.router, prefix="/api/v1")
app.include_router(reportes.router, prefix="/api/v1")
app.include_router(usuario.router, prefix="/api/v1")

# Servir interfaz web (dashboard) estático
_RUTA_STATIC = Path(__file__).parent / "static"
if _RUTA_STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(_RUTA_STATIC)), name="static")


@app.get("/", include_in_schema=False)
def inicio_dashboard():
    """Página principal: Panel visual interactivo de gestión."""
    archivo_index = _RUTA_STATIC / "index.html"
    if archivo_index.exists():
        return FileResponse(archivo_index)
    return RedirectResponse(url="/docs")


@app.get("/panel", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def redireccion_panel():
    """Redirige al panel visual principal."""
    return RedirectResponse(url="/")
