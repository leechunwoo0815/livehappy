"""
注册、登录、Token 刷新、登出、密码重置端点。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.redis import get_redis
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import BaseResponse
from app.schemas.user import UserResponse as UserResponseSchema
from app.services.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    get_stored_refresh_jti,
    hash_password,
    revoke_refresh_token,
    store_refresh_token,
    verify_password,
)
from app.services.user import get_user_by_email, get_user_by_id

router = APIRouter()


@router.post("/register", response_model=BaseResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ConflictException("邮箱已注册")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_id = str(user.id)
    access_token = create_access_token(user_id, user.role)
    refresh_token = create_refresh_token(user_id)

    refresh_payload = jwt.decode(
        refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    await store_refresh_token(user_id, refresh_payload.get("jti", ""))

    return BaseResponse(
        success=True,
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/login", response_model=BaseResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    redis = get_redis()
    rate_key = f"rate:login:{client_ip}"
    attempts = await redis.incr(rate_key)
    if attempts == 1:
        await redis.expire(rate_key, settings.login_rate_window)
    if attempts > settings.login_rate_limit:
        raise RateLimitException("登录尝试过于频繁，请稍后再试")

    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("邮箱或密码错误")

    user_id = str(user.id)
    access_token = create_access_token(user_id, user.role)
    refresh_token = create_refresh_token(user_id)

    refresh_payload = jwt.decode(
        refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    await store_refresh_token(user_id, refresh_payload.get("jti", ""))

    user.last_login = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()

    return BaseResponse(
        success=True,
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh", response_model=BaseResponse)
async def refresh(data: RefreshRequest):
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "refresh":
            raise UnauthorizedException()
        user_id = payload["sub"]
        jti = payload.get("jti", "")
    except JWTError:
        raise UnauthorizedException()

    stored_jti = await get_stored_refresh_jti(user_id)
    if not stored_jti or stored_jti != jti:
        raise UnauthorizedException("refresh_token 已失效")

    new_access = create_access_token(user_id)
    return BaseResponse(
        success=True,
        data=TokenResponse(access_token=new_access, refresh_token=data.refresh_token),
    )


@router.post("/logout", response_model=BaseResponse)
async def logout(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            jti = payload.get("jti")
            sub = payload.get("sub")
            exp = payload.get("exp", 0)
            now = datetime.now(UTC).timestamp()
            ttl = max(int(exp - now), 60)
            if jti:
                await blacklist_token(jti, ttl)
            if sub:
                await revoke_refresh_token(sub)
        except JWTError:
            pass
    return BaseResponse(success=True, message="已登出")


@router.get("/me", response_model=BaseResponse)
async def get_me(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, current_user_id)
    return BaseResponse(success=True, data=UserResponseSchema.model_validate(user))


@router.post("/forgot-password", response_model=BaseResponse)
async def forgot_password(
    email: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if not user:
        raise NotFoundException("该邮箱未注册")

    reset_token = str(uuid.uuid4())
    redis = get_redis()
    await redis.set(f"reset:{reset_token}", str(user.id), ex=3600)

    return BaseResponse(
        success=True,
        data={"reset_token": reset_token},
        message="重置链接已发送（Mock）",
    )


@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()
    user_id = await redis.get(f"reset:{token}")
    if not user_id:
        raise BadRequestException("重置链接已失效")

    user = await get_user_by_id(db, user_id)

    user.password_hash = hash_password(new_password)
    await db.commit()
    await redis.delete(f"reset:{token}")

    return BaseResponse(success=True, message="密码已重置")
