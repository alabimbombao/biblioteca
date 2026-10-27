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
    """Datos duplicados o borrar algo con dependientes (409)."""
    status_code = 409


class ReglaNegocio(ErrorAplicacion):
    """Una regla de la biblioteca no se cumple (422)."""
    status_code = 422
