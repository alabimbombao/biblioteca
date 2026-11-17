"""Rutas de libros."""

from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, File

from app.controllers import libros as ctrl
from app.controllers.libros import OrdenLibro
from app.core.cloudinary_client import eliminar_portada, subir_portada
from app.core.dependencies import PaginacionDep, SessionDep, SoloAdmin, Staff
from app.routes.respuestas import RESPUESTAS_ADMIN, RESPUESTAS_PUBLICAS, RESPUESTAS_STAFF
from app.schemas.libro import LibroCreate, LibroOut, LibroUpdate
from app.schemas.pagina import Pagina

router = APIRouter(tags=["Libros"])


@router.get(
    "/libros",
    response_model=Pagina[LibroOut],
    summary="Listar libros",
    responses=RESPUESTAS_PUBLICAS,
)
def listar(
    pag: PaginacionDep,
    db: SessionDep,
    buscar: Annotated[
        str | None, Query(description="Búsqueda por título")
    ] = None,
    autor: Annotated[
        str | None, Query(description="Filtro por nombre de autor")
    ] = None,
    categoria_id: Annotated[
        int | None, Query(description="Filtro por categoría")
    ] = None,
    desde: Annotated[
        int | None, Query(description="Año de publicación mínimo")
    ] = None,
    hasta: Annotated[
        int | None, Query(description="Año de publicación máximo")
    ] = None,
    orden: OrdenLibro | None = None,
):
    """Lista pública del catálogo con filtros y paginación."""
    items, total = ctrl.listar_libros(
        db,
        pag.skip,
        pag.limit,
        buscar,
        autor,
        categoria_id,
        desde,
        hasta,
        orden,
    )
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.get(
    "/libros/{libro_id}",
    response_model=LibroOut,
    summary="Obtener un libro",
    responses=RESPUESTAS_PUBLICAS,
)
def obtener(libro_id: int, db: SessionDep):
    """Devuelve un libro por su identificador."""
    return ctrl.obtener_libro(db, libro_id)


@router.post(
    "/libros",
    response_model=LibroOut,
    status_code=201,
    summary="Crear un libro",
    responses=RESPUESTAS_STAFF,
)
def crear(datos: LibroCreate, db: SessionDep, _usuario: Staff):
    """Crea un libro. Requiere rol bibliotecario o admin."""
    return ctrl.crear_libro(db, datos)


@router.patch(
    "/libros/{libro_id}",
    response_model=LibroOut,
    summary="Actualizar un libro",
    responses=RESPUESTAS_STAFF,
)
def actualizar(
    libro_id: int, datos: LibroUpdate, db: SessionDep, _usuario: Staff
):
    """Actualiza un libro. Requiere rol bibliotecario o admin."""
    return ctrl.actualizar_libro(db, libro_id, datos)


@router.delete(
    "/libros/{libro_id}",
    status_code=204,
    summary="Eliminar un libro",
    responses=RESPUESTAS_ADMIN,
)
def eliminar(libro_id: int, db: SessionDep, _usuario: SoloAdmin):
    """Elimina un libro. Solo el administrador puede hacerlo."""
    ctrl.eliminar_libro(db, libro_id)


@router.get(
    "/autores/{autor_id}/libros",
    response_model=Pagina[LibroOut],
    tags=["Autores"],
    summary="Listar los libros de un autor",
    responses=RESPUESTAS_PUBLICAS,
)
def libros_de_autor(autor_id: int, pag: PaginacionDep, db: SessionDep):
    """Lista pública de los libros de un autor."""
    items, total = ctrl.libros_de_autor(db, autor_id, pag.skip, pag.limit)
    return {
        "items": items,
        "total": total,
        "skip": pag.skip,
        "limit": pag.limit,
    }


@router.post(
    "/libros/{libro_id}/portada",
    response_model=LibroOut,
    summary="Subir portada de un libro",
    responses=RESPUESTAS_STAFF,
)
async def subir_portada_libro(
    libro_id: int,
    db: SessionDep,
    _usuario: Staff,
    archivo: Annotated[UploadFile, File(description="Imagen (jpg, png, webp · máx 5 MB)")],
):
    """Sube o reemplaza la portada de un libro en Cloudinary.

    Acepta jpg, jpeg, png y webp. Tamaño máximo 5 MB.
    Requiere rol bibliotecario o admin.
    """
    resultado = await subir_portada(archivo, libro_id)
    return ctrl.asignar_portada(
        db, libro_id, resultado["url"], resultado["public_id"]
    )


@router.delete(
    "/libros/{libro_id}/portada",
    response_model=LibroOut,
    summary="Eliminar portada de un libro",
    responses=RESPUESTAS_STAFF,
)
async def eliminar_portada_libro(
    libro_id: int,
    db: SessionDep,
    _usuario: Staff,
):
    """Elimina la portada de un libro de Cloudinary y borra su referencia.

    Requiere rol bibliotecario o admin.
    """
    libro = ctrl.obtener_libro(db, libro_id)
    if libro.portada_public_id:
        await eliminar_portada(libro.portada_public_id)
    return ctrl.quitar_portada(db, libro_id)
