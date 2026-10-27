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
