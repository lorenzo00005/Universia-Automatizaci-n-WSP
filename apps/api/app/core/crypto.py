"""Cifrado de secretos de terceros (tokens de Meta, Google, etc.) con Fernet."""

import hashlib
import secrets
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import String
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().encryption_key
    if not key:
        raise RuntimeError("Falta ENCRYPTION_KEY (generala con `make key`).")
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class EncryptedString(TypeDecorator[str]):
    """Columna de texto que se guarda cifrada y se lee descifrada."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        return None if value is None else encrypt(str(value))

    def process_result_value(self, value: Any, dialect: Dialect) -> str | None:
        return None if value is None else decrypt(str(value))
