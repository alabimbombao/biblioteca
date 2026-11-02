# Biblioteca API REST segura

API REST de la biblioteca construida con FastAPI, SQLAlchemy 2.0, PostgreSQL y
Alembic. Implementa autenticación con JWT (access y refresh token), autorización
por roles y por propiedad del recurso, contraseñas con hash Argon2, migraciones
versionadas, paginación, CORS, rate limiting y manejo controlado de errores.

> Taller 2 – API REST segura con FastAPI: autenticación, autorización y migraciones.

## Tecnologías

| Librería | Uso |
|---|---|
| `fastapi[standard]` | Framework, servidor y formulario OAuth2 |
| `sqlalchemy` 2.0 | ORM con `Mapped`, `mapped_column` y `select` |
| `psycopg[binary]` | Driver de PostgreSQL |
| `alembic` | Migraciones versionadas |
| `pydantic-settings` | Configuración tipada desde `.env` |
| `pyjwt` | Creación y verificación de JWT (HS256) |
| `pwdlib[argon2]` | Hash y verificación de contraseñas con Argon2 |
| `slowapi` | Límite de peticiones por minuto |

## Estructura

```text
biblioteca/
├── app/
│   ├── main.py                 routers, middlewares y manejadores de errores
│   ├── core/
│   │   ├── config.py           Settings con pydantic-settings
│   │   ├── database.py         engine, SessionLocal, Base y convención de nombres
│   │   ├── security.py         hash Argon2 y creación/lectura de JWT
│   │   ├── dependencies.py     SessionDep, CurrentUser, requiere_rol, paginación
│   │   ├── exceptions.py       excepciones propias
│   │   └── rate_limit.py       limitador de slowapi
│   ├── models/                 autores, categorías, libros, socios, préstamos,
│   │                           usuarios y refresh tokens
│   ├── schemas/                validación de entrada y respuestas
│   ├── controllers/            lógica de negocio (MVC)
│   ├── routes/                 endpoints y permisos
│   └── scripts/crear_admin.py  crea el primer administrador
├── alembic/
│   ├── env.py
│   └── versions/               una migración por cambio
├── tests/                      pruebas con pytest
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements-dev.txt
```

Copie `.env.example` como `.env` y complete los valores:

```bash
cp .env.example .env
```

Genere una `SECRET_KEY` segura (mínimo 32 caracteres):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Variables de entorno

| Variable | Ejemplo | Uso |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/biblioteca` | Conexión de la API |
| `TEST_DATABASE_URL` | `.../biblioteca_test` | Base exclusiva para pytest |
| `SECRET_KEY` | mínimo 32 caracteres | Firma de los JWT |
| `ALGORITHM` | `HS256` | Algoritmo de firma |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Duración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Duración del refresh token |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Frontends autorizados |
| `ENVIRONMENT` | `dev`, `test` o `prod` | Entorno de ejecución |

En producción no se permite `*` en `CORS_ORIGINS` y la documentación
interactiva se desactiva.

## Base de datos

Levante PostgreSQL con Docker:

```bash
docker compose up -d db
```

Cree la base de pruebas si va a ejecutar pytest:

```bash
createdb -U postgres biblioteca_test
```

## Migraciones

La aplicación **no** usa `Base.metadata.create_all`. Toda modificación de la
base se aplica con Alembic:

```bash
alembic upgrade head                                  # aplica todo
alembic downgrade -1                                  # revierte la última
alembic downgrade base                                # revierte todas
alembic current                                       # versión actual
alembic history                                       # historial
alembic revision --autogenerate -m "mensaje"          # nueva migración
```

Migraciones incluidas:

| Migración | Contenido |
|---|---|
| `0001_estado_inicial` | Tablas del Taller 1 |
| `0002_multa_pagada` | `prestamos.multa_pagada` y migración de datos |
| `0003_usuarios` | Tabla `usuarios`, tipo enum `rolusuario` y relación 1 a 1 con socios |
| `0004_refresh_tokens` | Tabla `refresh_tokens` |
| `0005_auditoria_prestamos` | `prestamos.registrado_por_id` (FK a usuarios) |

Antes de cada commit se recomienda verificar que
`alembic downgrade base` y `alembic upgrade head` funcionen sin errores.

## Primer administrador

Nadie puede registrarse como administrador desde la API. El primer admin se
crea por consola:

```bash
python -m app.scripts.crear_admin
```

El script pide email, nombre y contraseña con `getpass`. Si el email ya existe,
no modifica nada.

## Ejecución

```bash
fastapi dev app/main.py
```

- API: `http://127.0.0.1:8000/api/v1`
- Documentación: `http://127.0.0.1:8000/docs`
- Salud: `GET /api/v1/health`

## Datos de prueba

Con la API en marcha y el administrador ya creado:

```bash
python seeder.py --email-admin admin@biblioteca.com --password-admin Admin1234
```

El script inicia sesión con el administrador, crea el bibliotecario
`bibliotecario@biblioteca.com` (contraseña `Biblioteca123`), registra los
socios `ana.torres@example.com` y `luis.gomez@example.com` (contraseña
`Socio1234`) y carga autores, categorías, libros y préstamos. Es idempotente:
si un registro ya existe, lo reutiliza. `insertar_datos.py` se conserva como
alias del mismo flujo.

## Autenticación

1. `POST /api/v1/auth/login` con formulario OAuth2 (`username` = email).
2. La respuesta incluye `access_token`, `refresh_token`, `token_type` y
   `expires_in` (900 segundos por defecto).
3. Envíe el access token como `Authorization: Bearer <token>`.
4. Renueve con `POST /api/v1/auth/refresh`; el refresh token se rota y el
   anterior queda revocado.
5. `POST /api/v1/auth/logout` revoca el refresh token.

Contenido del JWT: `sub`, `rol`, `type` (`access` o `refresh`), `iat`, `exp` y
`jti`. El `jti` del refresh token se guarda en la tabla `refresh_tokens`.

Reglas de autenticación:

- Credenciales incorrectas: `401` con el mismo mensaje exista o no el email.
- Usuario inactivo: `403`.
- Después de 5 intentos fallidos: bloqueo de 15 minutos (`423`).
- Reutilizar un refresh token ya rotado revoca todos los tokens del usuario.
- Un refresh token no sirve como access token ni al revés.

## Roles

| Rol | Quién es | Qué puede hacer |
|---|---|---|
| anónimo | Sin token | Registrarse, iniciar sesión y consultar el catálogo |
| socio | Persona inscrita, vinculada a un registro de `socios` | Ver y editar su perfil, ver sus préstamos y sus multas |
| bibliotecario | Empleado de la biblioteca | Gestionar catálogo y socios, registrar préstamos, devoluciones y pagos, ver reportes |
| admin | Administrador | Todo lo anterior, borrar recursos y gestionar usuarios y roles |

Un socio solo accede a sus propios datos. Si consulta un préstamo ajeno recibe
`404` (no se revela que existe). En `GET /prestamos` el filtro `socio_id` se
ignora para los socios.

## Endpoints y permisos

| Método | Ruta | Anónimo | Socio | Bibliotecario | Admin |
|---|---|:---:|:---:|:---:|:---:|
| GET | `/api/v1/health` | Sí | Sí | Sí | Sí |
| POST | `/api/v1/auth/registro` | Sí | Sí | Sí | Sí |
| POST | `/api/v1/auth/login` | Sí | Sí | Sí | Sí |
| POST | `/api/v1/auth/refresh` | Sí | Sí | Sí | Sí |
| POST | `/api/v1/auth/logout` | No | Sí | Sí | Sí |
| GET | `/api/v1/auth/me` | No | Sí | Sí | Sí |
| PATCH | `/api/v1/auth/me/password` | No | Sí | Sí | Sí |
| GET | `/api/v1/libros`, `/autores`, `/categorias` | Sí | Sí | Sí | Sí |
| POST / PATCH | `/api/v1/libros`, `/autores`, `/categorias` | No | No | Sí | Sí |
| DELETE | `/api/v1/libros`, `/autores`, `/categorias` | No | No | No | Sí |
| GET | `/api/v1/socios` | No | No | Sí | Sí |
| POST | `/api/v1/socios` | No | No | Sí | Sí |
| GET / PATCH | `/api/v1/socios/me` | No | Propio | No | No |
| GET | `/api/v1/socios/me/prestamos` | No | Propio | No | No |
| GET | `/api/v1/socios/me/multas` | No | Propio | No | No |
| GET / PATCH | `/api/v1/socios/{id}` | No | No | Sí | Sí |
| DELETE | `/api/v1/socios/{id}` | No | No | No | Sí |
| GET | `/api/v1/prestamos`, `/prestamos/{id}` | No | Propio | Sí | Sí |
| POST | `/api/v1/prestamos` | No | No | Sí | Sí |
| POST | `/api/v1/prestamos/{id}/devolucion` | No | No | Sí | Sí |
| POST | `/api/v1/prestamos/{id}/pago-multa` | No | No | Sí | Sí |
| GET | `/api/v1/reportes/*` | No | No | Sí | Sí |
| GET / POST | `/api/v1/usuarios` | No | No | No | Sí |
| PATCH | `/api/v1/usuarios/{id}/rol` | No | No | No | Sí |
| PATCH | `/api/v1/usuarios/{id}/activo` | No | No | No | Sí |

Los listados responden:

```json
{ "items": [], "total": 0, "skip": 0, "limit": 10 }
```

El login responde:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Reglas de negocio

Se conservan las reglas R1 a R10 del Taller 1 y se agrega:

- **R11**: un socio con multas sin pagar no puede pedir préstamos (`422`
  «El socio tiene multas pendientes»).
- `POST /api/v1/prestamos/{id}/pago-multa`: marca la multa como pagada. Responde
  `409` si el préstamo no tiene multa o ya fue pagada.

Otras reglas relevantes:

- Un administrador no puede quitarse su propio rol ni desactivarse (`422`).
- Cambiar el rol o desactivar un usuario revoca sus refresh tokens.
- Al registrar un préstamo se guarda `registrado_por_id`.
- Los préstamos con multa cero quedan marcados como pagados por la migración
  `0002`.

## Protección y observabilidad

- **Rate limiting**: login 10 peticiones/minuto y registro 5/minuto por IP.
  Al superar el límite responde `429`.
- **Request ID**: cada respuesta incluye `X-Request-ID`; se registra método,
  ruta, código y duración en milisegundos. Nunca se registran contraseñas ni
  tokens.
- **Errores**: las excepciones propias devuelven `{ "detail": "..." }`; los
  errores no controlados devuelven `500` con un mensaje genérico y quedan en el
  log.
- **CORS**: configurado desde `CORS_ORIGINS`.
- **Documentación**: cada router tiene etiquetas y cada endpoint `summary` y
  respuestas documentadas.

## Pruebas

Las pruebas usan `TEST_DATABASE_URL` y reinician el contador de slowapi antes de
cada caso:

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

Se cubren registro, login, bloqueo por intentos, rotación y reutilización de
refresh tokens, permisos por rol, propiedad de préstamos, reglas de multas,
paginación, reportes y rate limiting.

## Docker

```bash
docker compose up -d db
docker compose up --build api
```

El contenedor de la API aplica `alembic upgrade head` antes de arrancar. La
`SECRET_KEY` y las demás variables se leen desde `.env`; la URL de la base se
sobrescribe dentro de la red de Docker para apuntar al servicio `db`.

## Integrantes

- Nombre y apellido del aprendiz
- Nombre y apellido del aprendiz
