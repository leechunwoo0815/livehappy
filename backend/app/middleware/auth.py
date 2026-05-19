"""
JWT 认证中间件 + get_current_user 依赖项。

JWTMiddleware：全局中间件，负责 Token 解析、黑名单检查、封禁检查。
get_current_user：路由级依赖项，从 request.state 提取 user_id。
"""

from __future__ import annotations

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import settings
from app.core.exceptions import UnauthorizedException
from app.redis import get_redis

EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/messages/ws",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
}


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request.state.user_id = None
        request.state.user_role = None

        path = request.url.path

        if path in EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except JWTError:
            return await call_next(request)

        if payload.get("type") != "access":
            return await call_next(request)

        jti = payload.get("jti")
        user_id = payload.get("sub")
        role = payload.get("role", "user")

        if jti:
            redis = get_redis()
            blacklisted = await redis.get(f"blacklist:{jti}")
            if blacklisted:
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "data": None,
                        "message": "Token 已失效",
                        "code": "TOKEN_REVOKED",
                    },
                )

        if user_id:
            redis = get_redis()
            banned = await redis.sismember("banned_users", user_id)
            if banned:
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "data": None,
                        "message": "账号已被封禁",
                        "code": "USER_BANNED",
                    },
                )

        request.state.user_id = user_id
        request.state.user_role = role

        return await call_next(request)


async def get_current_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise UnauthorizedException()
    return user_id
