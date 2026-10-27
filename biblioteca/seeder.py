"""
seeder.py – Carga datos de prueba variados para la Biblioteca API REST.
Ejecutar con la API en marcha:

    python seeder.py
"""

import requests

BASE = "http://127.0.0.1:8000"


def get(ruta, params=None):
    try:
        r = requests.get(f"{BASE}{ruta}", params=params)
        return r.json() if r.ok else None
    except Exception as e:
        print(f"  [ERROR CONEXION] GET {ruta}: {e}")
        return None


def post(ruta, datos):
    try:
        r = requests.post(f"{BASE}{ruta}", json=datos)
        if r.status_code in (200, 201):
            print(f"  [OK {r.status_code}] POST {ruta} -> Creado con ID: {r.json().get('id')}")
            return r.json()
        elif r.status_code == 409:
            # Si ya existe por restricción única, buscamos el registro existente
            print(f"  [INFO 409] POST {ruta} ya existía en la base de datos.")
            return buscar_existente(ruta, datos)
        else:
            print(f"  [ERR {r.status_code}] POST {ruta} -> {r.text}")
            return None
    except Exception as e:
        print(f"  [ERROR CONEXION] POST {ruta}: {e}")
        return None


def buscar_existente(ruta, datos):
    """Recupera el objeto si ya existía en la BD para no detener el seeder."""
    if "autores" in ruta:
        todos = get("/autores/?limit=100") or []
        return next((a for a in todos if a.get("nombre", "").lower() == datos.get("nombre", "").lower()), None)
    elif "categorias" in ruta:
        todos = get("/categorias/?limit=100") or []
        return next((c for c in todos if c.get("nombre", "").lower() == datos.get("nombre", "").lower()), None)
    elif "libros" in ruta:
        todos = get("/libros?limit=100") or []
        return next((l for l in todos if l.get("isbn") == datos.get("isbn")), None)
    elif "socios" in ruta:
        todos = get("/socios/?limit=100") or []
        return next((s for s in todos if s.get("email", "").lower() == datos.get("email", "").lower()), None)
    return None


print("=" * 60)
print("INICIANDO CARGA DE DATOS DE PRUEBA (SEEDER)")
print("=" * 60)

# ── 1. AUTORES ───────────────────────────────────────────────
print("\n>>> Cargando Autores...")
autores_datos = [
    {"nombre": "Julio Cortazar", "nacionalidad": "Argentina", "anio_nacimiento": 1914},
    {"nombre": "Mary Shelley", "nacionalidad": "Britanica", "anio_nacimiento": 1797},
    {"nombre": "Isaac Asimov", "nacionalidad": "Estadounidense", "anio_nacimiento": 1920},
    {"nombre": "Haruki Murakami", "nacionalidad": "Japonesa", "anio_nacimiento": 1949},
    {"nombre": "Jane Austen", "nacionalidad": "Britanica", "anio_nacimiento": 1775},
]

autores = {}
for a_data in autores_datos:
    res = post("/autores/", a_data)
    if res:
        autores[a_data["nombre"]] = res

# ── 2. CATEGORÍAS ─────────────────────────────────────────────
print("\n>>> Cargando Categorías...")
categorias_datos = [
    {"nombre": "Ciencia Ficcion", "descripcion": "Obras sobre tecnologia avanzada, viajes espaciales y futuros distopicos"},
    {"nombre": "Terror y Suspenso", "descripcion": "Relatos de horror cosmico, misterio gotico y tension psicologica"},
    {"nombre": "Realismo Magico", "descripcion": "Historias donde lo fantastico e irreal se percibe como parte de la realidad"},
    {"nombre": "Clasicos Universales", "descripcion": "Grandes obras consagradas de la literatura universal"},
    {"nombre": "Romance Historico", "descripcion": "Historias y dramas sentimentales ambientados en epocas pasadas"},
]

categorias = {}
for c_data in categorias_datos:
    res = post("/categorias/", c_data)
    if res:
        categorias[c_data["nombre"].lower()] = res

# ── 3. LIBROS ────────────────────────────────────────────────
print("\n>>> Cargando Libros...")
libros_datos = [
    {
        "titulo": "Rayuela",
        "isbn": "9788437604572",
        "anio_publicacion": 1963,
        "ejemplares": 4,
        "autor": "Julio Cortazar",
        "cats": ["clasicos universales", "realismo magico"],
    },
    {
        "titulo": "Frankenstein",
        "isbn": "9788467034073",
        "anio_publicacion": 1818,
        "ejemplares": 3,
        "autor": "Mary Shelley",
        "cats": ["terror y suspenso", "clasicos universales", "ciencia ficcion"],
    },
    {
        "titulo": "Fundacion",
        "isbn": "9788497599245",
        "anio_publicacion": 1951,
        "ejemplares": 5,
        "autor": "Isaac Asimov",
        "cats": ["ciencia ficcion", "clasicos universales"],
    },
    {
        "titulo": "Tokio Blues",
        "isbn": "9788483835159",
        "anio_publicacion": 1987,
        "ejemplares": 3,
        "autor": "Haruki Murakami",
        "cats": ["clasicos universales", "romance historico"],
    },
    {
        "titulo": "Orgullo y Prejuicio",
        "isbn": "9788497940856",
        "anio_publicacion": 1813,
        "ejemplares": 4,
        "autor": "Jane Austen",
        "cats": ["clasicos universales", "romance historico"],
    },
    {
        "titulo": "Yo Robot",
        "isbn": "9788435018364",
        "anio_publicacion": 1950,
        "ejemplares": 2,
        "autor": "Isaac Asimov",
        "cats": ["ciencia ficcion"],
    },
]

libros = {}
for l_data in libros_datos:
    autor_obj = autores.get(l_data["autor"])
    if not autor_obj:
        print(f"  [SKIP] Autor '{l_data['autor']}' no disponible.")
        continue

    cat_ids = [categorias[c_name]["id"] for c_name in l_data["cats"] if c_name in categorias]
    if not cat_ids:
        print(f"  [SKIP] No se encontraron categorias para '{l_data['titulo']}'.")
        continue

    payload = {
        "titulo": l_data["titulo"],
        "isbn": l_data["isbn"],
        "anio_publicacion": l_data["anio_publicacion"],
        "ejemplares": l_data["ejemplares"],
        "autor_id": autor_obj["id"],
        "categoria_ids": cat_ids,
    }
    res = post("/libros", payload)
    if res:
        libros[l_data["titulo"]] = res

# ── 4. SOCIOS ────────────────────────────────────────────────
print("\n>>> Cargando Socios...")
socios_datos = [
    {"nombre": "Carlos Mendoza", "email": "carlos.mendoza@example.com", "telefono": "+57 3119876543"},
    {"nombre": "Valentina Rios", "email": "valentina.rios@example.com", "telefono": "+57 3204567890"},
    {"nombre": "Santiago Morales", "email": "santiago.morales@example.com", "telefono": "+57 3156781234"},
    {"nombre": "Camila Herrera", "email": "camila.herrera@example.com", "telefono": "+57 3182345678"},
]

socios = {}
for s_data in socios_datos:
    res = post("/socios/", s_data)
    if res:
        socios[s_data["nombre"]] = res

# ── 5. PRÉSTAMOS ─────────────────────────────────────────────
print("\n>>> Creando Préstamos de Ejemplo...")
prestamos_ejemplo = [
    {"socio": "Carlos Mendoza", "libro": "Fundacion", "dias": 14},
    {"socio": "Valentina Rios", "libro": "Frankenstein", "dias": 7},
    {"socio": "Santiago Morales", "libro": "Rayuela", "dias": 21},
]

prestamos = []
for p_info in prestamos_ejemplo:
    socio_obj = socios.get(p_info["socio"])
    libro_obj = libros.get(p_info["libro"])
    if socio_obj and libro_obj:
        payload = {
            "socio_id": socio_obj["id"],
            "libro_id": libro_obj["id"],
            "dias": p_info["dias"],
        }
        res = post("/prestamos/", payload)
        if res:
            prestamos.append(res)
    else:
        print(f"  [SKIP] No se pudo crear préstamo de {p_info['libro']} para {p_info['socio']}.")

# ── RESUMEN FINAL ────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESUMEN DE DATOS CARGADOS")
print("=" * 60)
print(f"  - Autores registrados   : {len(autores)}")
print(f"  - Categorías registradas: {len(categorias)}")
print(f"  - Libros registrados    : {len(libros)}")
print(f"  - Socios registrados    : {len(socios)}")
print(f"  - Préstamos registrados : {len(prestamos)}")
print("=" * 60)
print("¡Seeder completado con éxito! Puedes consultar http://127.0.0.1:8000/docs\n")
