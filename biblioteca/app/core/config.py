"""Configuración central de la aplicación.

Toda la configuración se lee aquí con pydantic-settings. Ningún otro
archivo utiliza os.getenv ni load_dotenv.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno tipadas del proyecto."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/biblioteca_test"
    )
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = []
    environment: Literal["dev", "test", "prod"] = "dev"

    @property
    def es_produccion(self) -> bool:
        """Indica si la aplicación se ejecuta en producción."""
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia de la configuración."""
    return Settings()
