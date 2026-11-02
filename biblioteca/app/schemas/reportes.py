"""Esquemas de los reportes del Taller 1."""

from pydantic import BaseModel


class LibroMasPrestado(BaseModel):
    """Libro con su total de préstamos."""

    libro_id: int
    titulo: str
    autor: str
    total_prestamos: int

    model_config = {"from_attributes": True}


class CategoriaTotalLibros(BaseModel):
    """Cantidad de libros por categoría."""

    categoria_id: int
    nombre: str
    total_libros: int

    model_config = {"from_attributes": True}


class PrestamoVencido(BaseModel):
    """Préstamo sin devolver pasado su fecha límite."""

    prestamo_id: int
    titulo: str
    socio: str
    email: str
    fecha_limite: str
    dias_retraso: int

    model_config = {"from_attributes": True}


class SocioConMulta(BaseModel):
    """Socio con multas acumuladas."""

    socio_id: int
    nombre: str
    total_multas: float
    total_prestamos: int

    model_config = {"from_attributes": True}


class AutorReporte(BaseModel):
    """Totales de libros y préstamos por autor."""

    autor_id: int
    nombre: str
    total_libros: int
    total_ejemplares: int
    total_prestamos: int

    model_config = {"from_attributes": True}


class ResumenBiblioteca(BaseModel):
    """Resumen general de la biblioteca."""

    total_libros: int
    total_ejemplares: int
    total_prestados: int
    total_socios_activos: int
    total_socios_vencidos: int
    total_multas: float

    model_config = {"from_attributes": True}
