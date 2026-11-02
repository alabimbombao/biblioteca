"""Crea el primer administrador de la biblioteca.

Uso:
    python -m app.scripts.crear_admin

La contraseña se escribe por consola con getpass y nunca se guarda en el
código ni en una migración.
"""

import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hashear_password
from app.models.usuario import RolUsuario, Usuario
from app.schemas.usuario import validar_password_fuerte


def main() -> None:
    """Pide los datos por consola y crea el administrador si no existe."""
    print("=== Creación del administrador de la biblioteca ===")
    email = input("Email: ").strip().lower()
    nombre = input("Nombre: ").strip()
    password = getpass.getpass("Contraseña: ")
    confirmar = getpass.getpass("Confirmar contraseña: ")

    if password != confirmar:
        print("Error: las contraseñas no coinciden.")
        return

    try:
        validar_password_fuerte(password)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    with SessionLocal() as db:
        existe = db.scalar(select(Usuario).where(Usuario.email == email))
        if existe:
            print("Ya existe un usuario con ese email. No se hizo ningún cambio.")
            return

        usuario = Usuario(
            email=email,
            nombre=" ".join(nombre.split()).title(),
            password_hash=hashear_password(password),
            rol=RolUsuario.admin,
        )
        db.add(usuario)
        db.commit()

    print("Administrador creado correctamente.")


if __name__ == "__main__":
    main()
