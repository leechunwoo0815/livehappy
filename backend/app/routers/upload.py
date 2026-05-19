import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from app.config import settings
from app.core.exceptions import BadRequestException
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/upload", response_model=BaseResponse)
async def upload_file(
    file: UploadFile,
    user_id: str = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException("不支持的文件格式")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = upload_dir / filename
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise BadRequestException("文件过大")
    filepath.write_bytes(content)
    return BaseResponse(success=True, data={"url": f"/uploads/{filename}"})
