from pydantic import BaseModel
from typing import Optional


class LibroMasPrestado(BaseModel):
    libro_id: int
    titulo: str
    autor: str
    total_prestamos: int

    model_config = {"from_attributes": True}


class CategoriaTotalLibros(BaseModel):
    categoria_id: int
    nombre: str
    total_libros: int

    model_config = {"from_attributes": True}


class PrestamoVencido(BaseModel):
    prestamo_id: int
    titulo: str
    socio: str
    email: str
    fecha_limite: str
    dias_retraso: int

    model_config = {"from_attributes": True}


class SocioConMulta(BaseModel):
    socio_id: int
    nombre: str
    total_multas: float
    total_prestamos: int

    model_config = {"from_attributes": True}


class AutorReporte(BaseModel):
    autor_id: int
    nombre: str
    total_libros: int
    total_ejemplares: int
    total_prestamos: int

    model_config = {"from_attributes": True}


class ResumenBiblioteca(BaseModel):
    total_libros: int
    total_ejemplares: int
    total_prestados: int
    total_socios_activos: int
    total_socios_vencidos: int
    total_multas: float

    model_config = {"from_attributes": True}
