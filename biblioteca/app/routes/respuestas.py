"""Respuestas documentadas reutilizables en los routers."""

RESPUESTAS_AUTENTICADO = {
    401: {"description": "No autenticado o token inválido"},
}

RESPUESTAS_STAFF = {
    401: {"description": "No autenticado o token inválido"},
    403: {"description": "No tiene permisos para esta acción"},
    404: {"description": "Recurso no encontrado"},
}

RESPUESTAS_ADMIN = {
    401: {"description": "No autenticado o token inválido"},
    403: {"description": "Solo un administrador puede realizar esta acción"},
    404: {"description": "Recurso no encontrado"},
}

RESPUESTAS_PUBLICAS = {
    404: {"description": "Recurso no encontrado"},
}
