"""Configuración leída de variables de entorno (ver .env.example)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "Universia Automatización WSP"
    public_url: str = "http://localhost"
    # Prefijo bajo el que Caddy publica la API (para que /docs encuentre openapi.json).
    root_path: str = ""

    # Postgres: la app se conecta con un rol SIN privilegios de dueño para que RLS aplique.
    database_url: str = "postgresql+asyncpg://universia_app:universia_app@localhost:5432/universia"
    # Las migraciones corren con el dueño del esquema.
    database_migrations_url: str = (
        "postgresql+asyncpg://universia:universia@localhost:5432/universia"
    )
    redis_url: str = "redis://localhost:6379/0"

    # Clave Fernet para cifrar tokens de terceros en la base.
    encryption_key: str = Field(default="")
    session_cookie_name: str = "universia_session"
    session_ttl_hours: int = 24 * 14
    magic_link_ttl_minutes: int = 15

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    email_from: str = "Universia <hola@example.com>"

    sentry_dsn: str = ""
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
