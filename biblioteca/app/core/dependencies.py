from typing import Annotated, Generator
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


class Paginacion:
    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Registros a omitir"),
        limit: int = Query(default=10, ge=1, le=100, description="Max registros"),
    ):
        self.skip = skip
        self.limit = limit


PaginacionDep = Annotated[Paginacion, Depends()]
