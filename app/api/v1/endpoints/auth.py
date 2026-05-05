from fastapi import APIRouter, Depends
from jose import JWTError
from fastapi import HTTPException, status

from app.api.deps import DBSession
from app.core.constants import ErrorMessages, TokenType
from app.core.security import create_token_pair, decode_token
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# register with email and password
@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest, db: DBSession):
    return await auth_service.register_user(data, db)


# login with email and password
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DBSession):
    return await auth_service.login_user(data, db)


# authentication with google
@router.post("/google", response_model=TokenResponse)
async def google_login(data: GoogleAuthRequest, db: DBSession):
    return await auth_service.google_auth(data.id_token, db)


# refresh token for authentication
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != TokenType.REFRESH.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorMessages.INVALID_TOKEN,
            )
        user_id: str = payload.get("sub", "")
        role: str = payload.get("role", "user")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessages.INVALID_TOKEN
        )

    tokens = create_token_pair(user_id, role)
    return TokenResponse(**tokens)
