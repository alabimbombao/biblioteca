"""Compatibilidad con el nombre anterior del cargador de datos.

Todo el flujo autenticado vive en ``seeder.py``. Este archivo solo lo invoca
para no dejar un script antiguo que use endpoints sin autenticación.

Uso:
    python insertar_datos.py
"""

from seeder import main

if __name__ == "__main__":
    main()
