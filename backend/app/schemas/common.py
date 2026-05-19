"""
统一响应格式模型。

所有 API 响应必须遵循 BaseResponse 结构：
  成功: {"success": true, "data": {...}, "message": null}
  失败: {"success": false, "data": null, "message": "错误描述", "code": "ERROR_CODE"}
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):  # noqa: UP046
    success: bool
    data: T | None = None
    message: str | None = None
    code: str | None = None


class PaginatedData(BaseModel, Generic[T]):  # noqa: UP046
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
