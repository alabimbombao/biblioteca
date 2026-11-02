"""Excepciones propias de la aplicación."""


class ErrorAplicacion(Exception):
    """Clase base de todas las excepciones propias (400)."""

    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NoEncontrado(ErrorAplicacion):
    """El recurso no existe (404)."""

    status_code = 404


class Conflicto(ErrorAplicacion):
    """Datos duplicados o una operación repetida (409)."""

    status_code = 409


class ReglaNegocio(ErrorAplicacion):
    """Una regla de la biblioteca no se cumple (422)."""

    status_code = 422


class NoAutenticado(ErrorAplicacion):
    """Falta el token, es inválido, venció o es del tipo equivocado (401)."""

    status_code = 401


class Prohibido(ErrorAplicacion):
    """El usuario está autenticado pero no tiene permiso (403)."""

    status_code = 403


class CuentaBloqueada(ErrorAplicacion):
    """Demasiados intentos fallidos de inicio de sesión (423)."""

    status_code = 423


class ServicioNoDisponible(ErrorAplicacion):
    """La base de datos no responde (503)."""

    status_code = 503
