"""Worker de arq: procesa jobs lentos (emails hoy; LLM, STT, video y publicaciones después)."""

from email.message import EmailMessage
from typing import Any, ClassVar

import aiosmtplib
import structlog
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging

log = structlog.get_logger()


def build_magic_link_email(email: str, name: str, link: str) -> EmailMessage:
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = email
    msg["Subject"] = "Tu link para entrar a Universia"
    saludo = f"Hola {name}," if name else "Hola,"
    msg.set_content(
        f"{saludo}\n\n"
        f"Entrá al panel con este link (vence en {settings.magic_link_ttl_minutes} minutos):\n"
        f"{link}\n\n"
        "Si no lo pediste vos, ignorá este mail.\n\n— El equipo de Universia"
    )
    return msg


async def send_magic_link(ctx: dict[str, Any], email: str, name: str, link: str) -> None:
    settings = get_settings()
    await aiosmtplib.send(
        build_magic_link_email(email, name, link),
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_tls,
    )
    log.info("magic_link_sent", email=email)


async def ping(ctx: dict[str, Any]) -> str:
    return "pong"


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging(get_settings().log_level)
    log.info("worker_started")


class WorkerSettings:
    functions: ClassVar = [send_magic_link, ping]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
