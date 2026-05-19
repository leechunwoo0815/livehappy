"""
全局异常处理器，将所有异常转换为统一 BaseResponse 格式。

注册方式：在 main.py 中调用 register_exception_handlers(app)
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": str(exc.detail),
                "code": _http_status_to_code(exc.status_code),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            errors.append(f"{loc}: {err.get('msg', '')}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "message": "参数校验失败",
                "code": "VALIDATION_ERROR",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": "服务器内部错误",
                "code": "INTERNAL_ERROR",
            },
        )


def _http_status_to_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
    }
    return mapping.get(status_code, "UNKNOWN_ERROR")
