"""Punto de entrada de la API."""

import sentry_sdk
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.health.router import router as health_router
from app.domains.tenants.router import router as tenants_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)
    app = FastAPI(title=settings.app_name, version="0.1.0", root_path=settings.root_path)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(tenants_router)
    return app


app = create_app()
