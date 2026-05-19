"""
自定义异常体系，所有业务异常继承 AppException。

全局异常处理器（core/handlers.py）会捕获这些异常并转换为统一 BaseResponse 格式。
"""

from __future__ import annotations


class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int):
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, "NOT_FOUND", 404)


class ForbiddenException(AppException):
    def __init__(self, message: str = "无权访问"):
        super().__init__(message, "FORBIDDEN", 403)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)


class BadRequestException(AppException):
    def __init__(self, message: str, code: str = "BAD_REQUEST"):
        super().__init__(message, code, 400)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "未认证", code: str = "UNAUTHORIZED"):
        super().__init__(message, code, 401)


class RateLimitException(AppException):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)
