"""Carga datos de prueba en la API de la biblioteca.

Requiere que la API esté en marcha y que el administrador ya exista
(ver ``python -m app.scripts.crear_admin``). El script inicia sesión, crea un
bibliotecario, registra dos socios y carga autores, categorías, libros y
préstamos usando los endpoints protegidos de la versión 2 de la API.

Uso:
    python seeder.py
    python seeder.py --email-admin correo@ejemplo.com --password-admin Clave123
"""

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = "http://127.0.0.1:8000/api/v1"

EMAIL_BIBLIOTECARIO = "bibliotecario@biblioteca.com"
PASSWORD_BIBLIOTECARIO = "Biblioteca123"

AUTORES = [
    {"nombre": "Julio Cortazar", "nacionalidad": "Argentina", "anio_nacimiento": 1914},
    {"nombre": "Mary Shelley", "nacionalidad": "Britanica", "anio_nacimiento": 1797},
    {"nombre": "Isaac Asimov", "nacionalidad": "Estadounidense", "anio_nacimiento": 1920},
    {"nombre": "Haruki Murakami", "nacionalidad": "Japonesa", "anio_nacimiento": 1949},
    {"nombre": "Jane Austen", "nacionalidad": "Britanica", "anio_nacimiento": 1775},
]

CATEGORIAS = [
    {"nombre": "ciencia ficcion", "descripcion": "Tecnologia avanzada, viajes espaciales y futuros distopicos"},
    {"nombre": "terror y suspenso", "descripcion": "Horror cosmico, misterio gotico y tension psicologica"},
    {"nombre": "realismo magico", "descripcion": "Lo fantastico se percibe como parte de la realidad"},
    {"nombre": "clasicos universales", "descripcion": "Grandes obras consagradas de la literatura universal"},
    {"nombre": "romance historico", "descripcion": "Dramas sentimentales ambientados en epocas pasadas"},
]

LIBROS = [
    {
        "titulo": "Rayuela",
        "isbn": "9788437604572",
        "anio_publicacion": 1963,
        "ejemplares": 4,
        "autor": "Julio Cortazar",
        "categorias": ["clasicos universales", "realismo magico"],
    },
    {
        "titulo": "Frankenstein",
        "isbn": "9788467034073",
        "anio_publicacion": 1818,
        "ejemplares": 3,
        "autor": "Mary Shelley",
        "categorias": ["terror y suspenso", "clasicos universales", "ciencia ficcion"],
    },
    {
        "titulo": "Fundacion",
        "isbn": "9788497599245",
        "anio_publicacion": 1951,
        "ejemplares": 5,
        "autor": "Isaac Asimov",
        "categorias": ["ciencia ficcion", "clasicos universales"],
    },
    {
        "titulo": "Tokio Blues",
        "isbn": "9788483835159",
        "anio_publicacion": 1987,
        "ejemplares": 3,
        "autor": "Haruki Murakami",
        "categorias": ["clasicos universales", "romance historico"],
    },
    {
        "titulo": "Orgullo y Prejuicio",
        "isbn": "9788497940856",
        "anio_publicacion": 1813,
        "ejemplares": 4,
        "autor": "Jane Austen",
        "categorias": ["clasicos universales", "romance historico"],
    },
    {
        "titulo": "Yo Robot",
        "isbn": "9788435018364",
        "anio_publicacion": 1950,
        "ejemplares": 2,
        "autor": "Isaac Asimov",
        "categorias": ["ciencia ficcion"],
    },
]

SOCIOS = [
    {"nombre": "Ana Torres", "email": "ana.torres@example.com", "telefono": "+57 3001234567"},
    {"nombre": "Luis Gomez", "email": "luis.gomez@example.com", "telefono": "+57 3107654321"},
]

PRESTAMOS = [
    {"socio": "ana.torres@example.com", "libro": "Fundacion", "dias": 14},
    {"socio": "luis.gomez@example.com", "libro": "Frankenstein", "dias": 7},
    {"socio": "ana.torres@example.com", "libro": "Rayuela", "dias": 21},
]


def peticion(
    metodo: str,
    ruta: str,
    datos: dict | None = None,
    token: str | None = None,
    formulario: bool = False,
    parametros: dict | None = None,
) -> tuple[int, Any]:
    """Realiza una petición HTTP y devuelve el código y el cuerpo."""
    url = BASE + ruta
    if parametros:
        url = f"{url}?{urllib.parse.urlencode(parametros)}"

    cabeceras: dict[str, str] = {}
    cuerpo: bytes | None = None

    if datos is not None:
        if formulario:
            cuerpo = urllib.parse.urlencode(datos).encode("utf-8")
            cabeceras["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            cuerpo = json.dumps(datos).encode("utf-8")
            cabeceras["Content-Type"] = "application/json"

    if token:
        cabeceras["Authorization"] = f"Bearer {token}"

    solicitud = urllib.request.Request(
        url, data=cuerpo, headers=cabeceras, method=metodo
    )

    try:
        with urllib.request.urlopen(solicitud) as respuesta:
            texto = respuesta.read().decode("utf-8")
            return respuesta.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as error:
        texto = error.read().decode("utf-8")
        try:
            detalle = json.loads(texto) if texto else None
        except json.JSONDecodeError:
            detalle = texto
        return error.code, detalle
    except urllib.error.URLError as error:
        raise SystemExit(
            f"No se pudo conectar con la API en {BASE}: {error.reason}\n"
            "Inicie el servidor con: fastapi dev app/main.py"
        ) from error


def exigir_exito(
    codigo: int,
    cuerpo: Any,
    descripcion: str,
    codigos: tuple[int, ...] = (200, 201),
) -> None:
    """Detiene el script si la respuesta no es la esperada."""
    if codigo not in codigos:
        raise SystemExit(f"Error al {descripcion}: HTTP {codigo} -> {cuerpo}")


def iniciar_sesion(email: str, password: str) -> str:
    """Inicia sesión con el flujo OAuth2 y devuelve el access token."""
    codigo, cuerpo = peticion(
        "POST",
        "/auth/login",
        {"username": email, "password": password},
        formulario=True,
    )
    exigir_exito(codigo, cuerpo, f"iniciar sesión como {email}", (200,))
    return cuerpo["access_token"]


def listar_todos(ruta: str, token: str) -> list[dict]:
    """Recorre todas las páginas de un listado paginado."""
    elementos: list[dict] = []
    salto = 0

    while True:
        codigo, cuerpo = peticion(
            "GET",
            ruta,
            token=token,
            parametros={"skip": salto, "limit": 100},
        )
        exigir_exito(codigo, cuerpo, f"listar {ruta}")
        elementos.extend(cuerpo["items"])
        salto += 100
        if salto >= cuerpo["total"]:
            return elementos


def asegurar_bibliotecario(token_admin: str) -> None:
    """Crea el usuario bibliotecario si todavía no existe."""
    codigo, cuerpo = peticion(
        "POST",
        "/usuarios",
        {
            "email": EMAIL_BIBLIOTECARIO,
            "nombre": "Bibliotecario de Pruebas",
            "password": PASSWORD_BIBLIOTECARIO,
            "rol": "bibliotecario",
        },
        token=token_admin,
    )
    if codigo == 201:
        print(f"  [CREADO] Bibliotecario {EMAIL_BIBLIOTECARIO}")
    elif codigo == 409:
        print(f"  [EXISTE] Bibliotecario {EMAIL_BIBLIOTECARIO}")
    else:
        exigir_exito(codigo, cuerpo, "crear el bibliotecario")


def asegurar_socios(token: str) -> dict[str, dict]:
    """Registra los socios de prueba y devuelve sus datos por email."""
    existentes = listar_todos("/socios", token)
    socios: dict[str, dict] = {}

    for datos in SOCIOS:
        email = datos["email"].lower()
        encontrado = next(
            (socio for socio in existentes if socio["email"] == email), None
        )
        if encontrado:
            socios[email] = encontrado
            print(f"  [EXISTE] Socio {email}")
            continue

        codigo, cuerpo = peticion(
            "POST",
            "/auth/registro",
            {**datos, "password": "Socio1234", "confirmar_password": "Socio1234"},
        )
        if codigo == 201:
            socio = next(
                (s for s in listar_todos("/socios", token) if s["email"] == email),
                None,
            )
            if socio is None:
                raise SystemExit(f"No se encontró el socio recién creado {email}")
            socios[email] = socio
            print(f"  [CREADO] Socio {email}")
        elif codigo == 409:
            print(f"  [INFO] El email {email} ya estaba registrado")
        else:
            exigir_exito(codigo, cuerpo, f"registrar el socio {email}")

    return socios


def cargar_autores(token: str) -> dict[str, dict]:
    """Crea los autores que aún no existan."""
    existentes = listar_todos("/autores", token)
    autores: dict[str, dict] = {}

    for datos in AUTORES:
        encontrado = next(
            (a for a in existentes if a["nombre"].lower() == datos["nombre"].lower()),
            None,
        )
        if encontrado:
            autores[datos["nombre"]] = encontrado
            continue

        codigo, cuerpo = peticion("POST", "/autores", datos, token=token)
        exigir_exito(codigo, cuerpo, f"crear el autor {datos['nombre']}")
        autores[datos["nombre"]] = cuerpo
        print(f"  [CREADO] Autor {datos['nombre']}")

    return autores


def cargar_categorias(token: str) -> dict[str, dict]:
    """Crea las categorías que aún no existan."""
    existentes = listar_todos("/categorias", token)
    categorias: dict[str, dict] = {}

    for datos in CATEGORIAS:
        encontrada = next(
            (c for c in existentes if c["nombre"].lower() == datos["nombre"].lower()),
            None,
        )
        if encontrada:
            categorias[datos["nombre"]] = encontrada
            continue

        codigo, cuerpo = peticion("POST", "/categorias", datos, token=token)
        exigir_exito(codigo, cuerpo, f"crear la categoría {datos['nombre']}")
        categorias[datos["nombre"]] = cuerpo
        print(f"  [CREADO] Categoría {datos['nombre']}")

    return categorias


def cargar_libros(
    token: str,
    autores: dict[str, dict],
    categorias: dict[str, dict],
) -> dict[str, dict]:
    """Crea los libros que aún no existan."""
    existentes = listar_todos("/libros", token)
    libros: dict[str, dict] = {}

    for datos in LIBROS:
        encontrado = next(
            (libro for libro in existentes if libro["isbn"] == datos["isbn"]),
            None,
        )
        if encontrado:
            libros[datos["titulo"]] = encontrado
            continue

        autor = autores.get(datos["autor"])
        if autor is None:
            print(f"  [OMITIDO] Autor no disponible para {datos['titulo']}")
            continue

        categoria_ids = [
            categorias[nombre]["id"]
            for nombre in datos["categorias"]
            if nombre in categorias
        ]
        if not categoria_ids:
            print(f"  [OMITIDO] Sin categorías para {datos['titulo']}")
            continue

        codigo, cuerpo = peticion(
            "POST",
            "/libros",
            {
                "titulo": datos["titulo"],
                "isbn": datos["isbn"],
                "anio_publicacion": datos["anio_publicacion"],
                "ejemplares": datos["ejemplares"],
                "autor_id": autor["id"],
                "categoria_ids": categoria_ids,
            },
            token=token,
        )
        exigir_exito(codigo, cuerpo, f"crear el libro {datos['titulo']}")
        libros[datos["titulo"]] = cuerpo
        print(f"  [CREADO] Libro {datos['titulo']}")

    return libros


def cargar_prestamos(
    token: str,
    socios: dict[str, dict],
    libros: dict[str, dict],
) -> list[dict]:
    """Crea préstamos activos de ejemplo si no existen."""
    existentes = listar_todos("/prestamos", token)
    prestamos: list[dict] = []

    for datos in PRESTAMOS:
        socio = socios.get(datos["socio"])
        libro = libros.get(datos["libro"])
        if socio is None or libro is None:
            print(f"  [OMITIDO] Faltan datos para el préstamo de {datos['libro']}")
            continue

        activo = next(
            (
                p
                for p in existentes
                if p["socio_id"] == socio["id"]
                and p["libro_id"] == libro["id"]
                and p["fecha_devolucion"] is None
            ),
            None,
        )
        if activo:
            prestamos.append(activo)
            print(f"  [EXISTE] Préstamo de {datos['libro']} para {datos['socio']}")
            continue

        codigo, cuerpo = peticion(
            "POST",
            "/prestamos",
            {"socio_id": socio["id"], "libro_id": libro["id"], "dias": datos["dias"]},
            token=token,
        )
        exigir_exito(codigo, cuerpo, f"crear el préstamo de {datos['libro']}")
        existentes.append(cuerpo)
        prestamos.append(cuerpo)
        print(f"  [CREADO] Préstamo de {datos['libro']} para {datos['socio']}")

    return prestamos


def main() -> None:
    """Ejecuta la carga completa de datos de prueba."""
    global BASE

    analizador = argparse.ArgumentParser(description="Carga datos de prueba en la API")
    analizador.add_argument(
        "--url",
        default=BASE,
        help="URL base de la API (por defecto: %(default)s)",
    )
    analizador.add_argument("--email-admin", default="admin@biblioteca.com")
    analizador.add_argument("--password-admin", default="Admin1234")
    argumentos = analizador.parse_args()

    BASE = argumentos.url.rstrip("/")

    print("=" * 60)
    print("CARGA DE DATOS DE PRUEBA")
    print("=" * 60)

    print("\n>>> Autenticando al administrador...")
    token_admin = iniciar_sesion(argumentos.email_admin, argumentos.password_admin)

    print("\n>>> Preparando usuarios...")
    asegurar_bibliotecario(token_admin)
    token_staff = iniciar_sesion(EMAIL_BIBLIOTECARIO, PASSWORD_BIBLIOTECARIO)
    socios = asegurar_socios(token_staff)

    print("\n>>> Cargando autores...")
    autores = cargar_autores(token_staff)

    print("\n>>> Cargando categorías...")
    categorias = cargar_categorias(token_staff)

    print("\n>>> Cargando libros...")
    libros = cargar_libros(token_staff, autores, categorias)

    print("\n>>> Creando préstamos...")
    prestamos = cargar_prestamos(token_staff, socios, libros)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Autores    : {len(autores)}")
    print(f"  Categorías : {len(categorias)}")
    print(f"  Libros     : {len(libros)}")
    print(f"  Socios     : {len(socios)}")
    print(f"  Préstamos  : {len(prestamos)}")
    print("-" * 60)
    print(f"  Bibliotecario: {EMAIL_BIBLIOTECARIO} / {PASSWORD_BIBLIOTECARIO}")
    for datos in SOCIOS:
        print(f"  Socio        : {datos['email']} / Socio1234")
    print("=" * 60)


if __name__ == "__main__":
    main()
