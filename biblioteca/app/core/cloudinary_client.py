"""Cliente de Cloudinary para gestión de portadas de libros.

Configura el SDK una sola vez (patrón singleton mediante import) y expone
dos funciones públicas: subir_portada (async) y eliminar_portada (async).

IMPORTANTE: cloudinary.uploader.upload/destroy son operaciones de I/O
bloqueantes. Se ejecutan en el thread pool del event loop mediante
asyncio.get_event_loop().run_in_executor para no bloquear uvicorn.
"""

import asyncio
import logging
from functools import partial

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

logger = logging.getLogger("biblioteca.cloudinary")

_cfg = get_settings()

cloudinary.config(
    cloud_name=_cfg.cloudinary_cloud_name,
    api_key=_cfg.cloudinary_api_key,
    api_secret=_cfg.cloudinary_api_secret,
    secure=True,
)

_CARPETA = "biblioteca/portadas"
_FORMATOS_PERMITIDOS = {"jpg", "jpeg", "png", "webp"}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_TRANSFORMACION = [
    {"width": 400, "height": 600, "crop": "fill", "gravity": "auto"},
    {"quality": "auto:good", "fetch_format": "auto"},
]


async def subir_portada(archivo: UploadFile, libro_id: int) -> dict:
    """Sube una imagen como portada y devuelve url y public_id.

    La carga a Cloudinary (I/O síncrono) se delega al thread pool del
    event loop para no bloquear el servidor.

    Args:
        archivo: Archivo recibido por el endpoint (UploadFile de FastAPI).
        libro_id: Se usa como public_id determinista para facilitar
                  la sobreescritura sin acumular assets huérfanos.

    Returns:
        dict con 'url' (str HTTPS) y 'public_id' (str).

    Raises:
        HTTPException 400: formato no permitido o tamaño excedido.
        HTTPException 502: fallo al comunicarse con Cloudinary.
    """
    extension = (archivo.filename or "").rsplit(".", 1)[-1].lower()
    if extension not in _FORMATOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Use: {', '.join(sorted(_FORMATOS_PERMITIDOS))}",
        )

    contenido = await archivo.read()
    if len(contenido) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar los 5 MB",
        )

    public_id = f"{_CARPETA}/libro_{libro_id}"

    # Ejecutar la operación bloqueante de Cloudinary en el thread pool
    loop = asyncio.get_event_loop()
    _upload = partial(
        cloudinary.uploader.upload,
        contenido,
        public_id=public_id,
        overwrite=True,
        invalidate=True,          # invalida la CDN cache al sobreescribir
        resource_type="image",
        transformation=_TRANSFORMACION,
    )
    try:
        resultado = await loop.run_in_executor(None, _upload)
    except Exception as exc:
        logger.error("Error al subir portada libro_%s a Cloudinary: %s", libro_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al subir imagen a Cloudinary. Intente de nuevo.",
        ) from exc

    logger.info("Portada libro_%s subida: %s", libro_id, resultado["secure_url"])
    return {
        "url": resultado["secure_url"],
        "public_id": resultado["public_id"],
    }


async def eliminar_portada(public_id: str) -> None:
    """Elimina un asset de Cloudinary por su public_id (no-op si no existe).

    La operación bloqueante se delega al thread pool del event loop.

    Raises:
        HTTPException 502: si Cloudinary devuelve un error inesperado.
    """
    loop = asyncio.get_event_loop()
    _destroy = partial(
        cloudinary.uploader.destroy,
        public_id,
        resource_type="image",
        invalidate=True,
    )
    try:
        resultado = await loop.run_in_executor(None, _destroy)
        # Cloudinary devuelve {"result": "ok"} o {"result": "not found"}
        if resultado.get("result") not in ("ok", "not found"):
            raise RuntimeError(f"Respuesta inesperada: {resultado}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error al eliminar portada '%s' de Cloudinary: %s", public_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al eliminar imagen de Cloudinary.",
        ) from exc

    logger.info("Portada '%s' eliminada de Cloudinary", public_id)
