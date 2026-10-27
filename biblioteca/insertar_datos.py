"""
insertar_datos.py
=================
Inserta UN dato por tabla usando la API REST en ejecucion.
Requiere que la API este corriendo en http://127.0.0.1:8000

Uso:
    python insertar_datos.py
"""

import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"


def get(ruta: str) -> dict | list | None:
    url = BASE + ruta
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return None


def post(ruta: str, datos: dict) -> dict | None:
    url = BASE + ruta
    body = json.dumps(datos).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"  [OK {resp.status}] POST {ruta}")
            print(f"         -> {json.dumps(result, ensure_ascii=False)}")
            return result
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"  [ERR {e.code}] POST {ruta}")
        print(f"         -> {body_err}")
        return None


# ── 1. Autor ─────────────────────────────────────────────────
print("\n[1] Creando autor...")
_AUTOR_NOMBRE = "Gabriel Garcia Marquez"
autor = post("/autores/", {
    "nombre": _AUTOR_NOMBRE,
    "nacionalidad": "Colombiana",
    "anio_nacimiento": 1927
})
if autor is None:
    # Puede que ya exista → buscarlo
    todos = get("/autores/") or []
    autor = next((a for a in todos if a["nombre"] == _AUTOR_NOMBRE), None)
    if autor:
        print(f"  [EXISTE] Autor recuperado: id={autor['id']}")

# ── 2. Categoría ─────────────────────────────────────────────
print("\n[2] Creando categoria...")
_CAT_NOMBRE = "novela"
categoria = post("/categorias/", {
    "nombre": _CAT_NOMBRE,
    "descripcion": "Obras narrativas de ficcion"
})
if categoria is None:
    todos = get("/categorias/") or []
    categoria = next((c for c in todos if c["nombre"].lower() == _CAT_NOMBRE.lower()), None)
    if categoria:
        print(f"  [EXISTE] Categoria recuperada: id={categoria['id']}")

# ── 3. Libro ─────────────────────────────────────────────────
print("\n[3] Creando libro...")
_ISBN = "9780307474728"
libro = None
if autor and categoria:
    libro = post("/libros", {
        "titulo": "Cien Anos de Soledad",
        "isbn": _ISBN,
        "anio_publicacion": 1967,
        "ejemplares": 3,
        "autor_id": autor["id"],
        "categoria_ids": [categoria["id"]]
    })
    if libro is None:
        todos = get("/libros") or []
        libro = next((l for l in todos if l["isbn"] == _ISBN), None)
        if libro:
            print(f"  [EXISTE] Libro recuperado: id={libro['id']}")
else:
    print("  [SKIP] Necesita autor y categoria validos")

# ── 4. Socio ─────────────────────────────────────────────────
print("\n[4] Creando socio...")
_EMAIL = "ana.torres@example.com"
socio = post("/socios/", {
    "nombre": "Ana Torres",
    "email": _EMAIL,
    "telefono": "+57 3001234567"
})
if socio is None:
    todos = get("/socios/") or []
    socio = next((s for s in todos if s["email"] == _EMAIL), None)
    if socio:
        print(f"  [EXISTE] Socio recuperado: id={socio['id']}")

# ── 5. Préstamo ──────────────────────────────────────────────
print("\n[5] Creando prestamo...")
prestamo = None
if socio and libro:
    from datetime import date, timedelta
    prestamo = post("/prestamos/", {
        "socio_id": socio["id"],
        "libro_id": libro["id"],
        "dias": 14
    })
    if prestamo is None:
        # Puede que ya exista un prestamo activo del mismo socio/libro
        todos = get(f"/prestamos/?socio_id={socio['id']}&libro_id={libro['id']}") or []
        prestamo = next(
            (p for p in todos if p.get("fecha_devolucion") is None), None
        )
        if prestamo:
            print(f"  [EXISTE] Prestamo recuperado: id={prestamo['id']}")
else:
    print("  [SKIP] Necesita socio y libro validos")

# ── Resumen ───────────────────────────────────────────────────
print("\n" + "=" * 55)
print("RESUMEN")
print("=" * 55)
ids = {
    "autores":   autor["id"]    if autor    else "ERROR",
    "categorias":categoria["id"] if categoria else "ERROR",
    "libros":    libro["id"]    if libro    else "ERROR",
    "socios":    socio["id"]    if socio    else "ERROR",
    "prestamos": prestamo["id"] if prestamo else "ERROR",
}
for tabla, id_ in ids.items():
    estado = "OK" if isinstance(id_, int) else "FALLO"
    print(f"  [{estado}] {tabla:<12} id={id_}")

print("\nAbre pgAdmin, haz clic derecho en cada tabla -> Refresh")
print("O revisa en: http://127.0.0.1:8000/docs")
print()
