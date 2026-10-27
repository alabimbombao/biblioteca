# Biblioteca API REST

API REST completa para gestionar una biblioteca con FastAPI, SQLAlchemy y PostgreSQL.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env             # Editar con tus credenciales
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

## Endpoints

| Recurso       | Rutas base         |
|---------------|--------------------|
| Autores       | /autores           |
| Categorías    | /categorias        |
| Libros        | /libros            |
| Socios        | /socios            |
| Préstamos     | /prestamos         |
| Reportes      | /reportes          |
