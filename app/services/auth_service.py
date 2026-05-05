import uuid

from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import ErrorMessages, UserRole
from app.core.security import create_token_pair, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register_user(data: RegisterRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ErrorMessages.EMAIL_ALREADY_EXISTS)

    is_admin = data.email.lower() == settings.ADMIN_EMAIL.lower()
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.ADMIN if is_admin else UserRole.USER,
    )
    db.add(user)
    await db.flush()

    tokens = create_token_pair(str(user.id), user.role.value)
    return TokenResponse(**tokens)


async def login_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessages.INVALID_CREDENTIALS)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMessages.INACTIVE_USER)

    tokens = create_token_pair(str(user.id), user.role.value)
    return TokenResponse(**tokens)


async def google_auth(id_token_str: str, db: AsyncSession) -> TokenResponse:
    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessages.GOOGLE_AUTH_FAILED)

    google_id = idinfo["sub"]
    email = idinfo.get("email", "")
    full_name = idinfo.get("name")
    avatar_url = idinfo.get("picture")

    # Find by google_id first, then by email
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # Link Google account to existing email account
            user.google_id = google_id
            if not user.avatar_url:
                user.avatar_url = avatar_url
        else:
            # Create new user
            is_admin = email.lower() == settings.ADMIN_EMAIL.lower()
            user = User(
                email=email,
                google_id=google_id,
                full_name=full_name,
                avatar_url=avatar_url,
                role=UserRole.ADMIN if is_admin else UserRole.USER,
            )
            db.add(user)
            await db.flush()

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMessages.INACTIVE_USER)

    tokens = create_token_pair(str(user.id), user.role.value)
    return TokenResponse(**tokens)
