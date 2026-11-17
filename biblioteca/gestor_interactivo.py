"""Gestor interactivo por consola de la Biblioteca.

Permite listar, crear, actualizar y eliminar libros, autores, categorías,
socios y préstamos de forma guiada y visual en la terminal.

Uso:
    python gestor_interactivo.py
"""

import os
import sys
import webbrowser
from app.core.database import SessionLocal
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.socio import Socio
from app.models.prestamo import Prestamo
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def pausa():
    input("\nPresiona ENTER para continuar...")


def listar_libros(db):
    libros = db.scalars(
        select(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .order_by(Libro.titulo)
    ).all()

    print("\n" + "=" * 80)
    print("📚 CATÁLOGO DE LIBROS REGISTRADOS".center(80))
    print("=" * 80)
    if not libros:
        print("  (No hay libros registrados aún)")
        return

    print(f"{'ID':<4} | {'TÍTULO':<30} | {'AUTOR':<20} | {'EJEMPLARES':<10} | {'AÑO':<6}")
    print("-" * 80)
    for l in libros:
        autor_nom = l.autor.nombre if l.autor else "Sin autor"
        print(f"{l.id:<4} | {l.titulo[:28]:<30} | {autor_nom[:18]:<20} | {l.ejemplares:<10} | {l.anio_publicacion:<6}")


def crear_libro(db):
    print("\n--- CREAR NUEVO LIBRO ---")
    autores = db.scalars(select(Autor).order_by(Autor.nombre)).all()
    if not autores:
        print("⚠️ Primero debes crear al menos un autor.")
        return

    categorias = db.scalars(select(Categoria).order_by(Categoria.nombre)).all()
    if not categorias:
        print("⚠️ Primero debes crear al menos una categoría.")
        return

    titulo = input("Título del libro: ").strip()
    if not titulo:
        print("Título no puede estar vacío.")
        return

    isbn = input("ISBN (13 dígitos numéricos): ").strip()
    if len(isbn) != 13 or not isbn.isdigit():
        print("⚠️ El ISBN debe tener 13 dígitos numéricos.")
        return

    try:
        anio = int(input("Año de publicación (ej: 2020): "))
        ejemplares = int(input("Cantidad de ejemplares (1 a 50): "))
    except ValueError:
        print("⚠️ Valores numéricos inválidos.")
        return

    print("\nAutores disponibles:")
    for a in autores:
        print(f"  [{a.id}] {a.nombre} ({a.nacionalidad or 'N/A'})")
    try:
        autor_id = int(input("Selecciona el ID del autor: "))
    except ValueError:
        print("ID inválido.")
        return

    print("\nCategorías disponibles:")
    for c in categorias:
        print(f"  [{c.id}] {c.nombre}")
    cat_ids_str = input("IDs de categorías separados por coma (ej: 1, 2): ")
    try:
        cat_ids = [int(x.strip()) for x in cat_ids_str.split(",") if x.strip()]
    except ValueError:
        print("Formato de categorías inválido.")
        return

    from app.controllers import libros as ctrl
    from app.schemas.libro import LibroCreate

    try:
        datos = LibroCreate(
            titulo=titulo,
            isbn=isbn,
            anio_publicacion=anio,
            ejemplares=ejemplares,
            autor_id=autor_id,
            categoria_ids=cat_ids,
        )
        nuevo = ctrl.crear_libro(db, datos)
        print(f"\n✅ Libro '{nuevo.titulo}' creado exitosamente con ID #{nuevo.id}!")
    except Exception as e:
        print(f"\n❌ Error al crear libro: {e}")


def eliminar_libro(db):
    listar_libros(db)
    try:
        libro_id = int(input("\nIngresa el ID del libro que deseas eliminar: "))
    except ValueError:
        print("ID inválido.")
        return

    from app.controllers import libros as ctrl
    try:
        ctrl.eliminar_libro(db, libro_id)
        print(f"\n✅ Libro #{libro_id} eliminado exitosamente.")
    except Exception as e:
        print(f"\n❌ No se pudo eliminar: {e}")


def main():
    while True:
        limpiar()
        print("=" * 60)
        print("   SISTEMA DE GESTIÓN DE BIBLIOTECA - CONSOLA INTUITIVA")
        print("=" * 60)
        print("1. 📚 Listar libros en catálogo")
        print("2. ➕ Registrar nuevo libro (guiado)")
        print("3. 🗑️  Eliminar libro por ID")
        print("4. 🌐 Abrir Panel Visual Web en el Navegador (http://127.0.0.1:8000)")
        print("5. 🚪 Salir")
        print("-" * 60)
        opcion = input("Selecciona una opción (1-5): ").strip()

        db = SessionLocal()
        try:
            if opcion == "1":
                listar_libros(db)
                pausa()
            elif opcion == "2":
                crear_libro(db)
                pausa()
            elif opcion == "3":
                eliminar_libro(db)
                pausa()
            elif opcion == "4":
                print("Abriendo http://127.0.0.1:8000 en tu navegador...")
                webbrowser.open("http://127.0.0.1:8000")
                pausa()
            elif opcion == "5":
                print("¡Hasta pronto!")
                break
        finally:
            db.close()


if __name__ == "__main__":
    main()
