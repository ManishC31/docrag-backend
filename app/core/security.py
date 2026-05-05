import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings
from app.core.constants import TokenType


def _prehash(password: str) -> bytes:
    # SHA-256 + base64 = 44 bytes, safely under bcrypt's 72-byte limit
    return base64.b64encode(hashlib.sha256(password.encode()).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode())


def create_token(subject: str, token_type: TokenType, extra_data: dict[str, Any] | None = None) -> str:
    if token_type == TokenType.ACCESS:
        expire_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.now(timezone.utc) + expire_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "type": token_type.value,
    }
    if extra_data:
        payload.update(extra_data)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def create_token_pair(user_id: str, role: str) -> dict[str, str]:
    extra = {"role": role}
    return {
        "access_token": create_token(user_id, TokenType.ACCESS, extra),
        "refresh_token": create_token(user_id, TokenType.REFRESH, extra),
        "token_type": "bearer",
    }
