from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.schemas.social import NoteCreate
from app.services.social import (
    add_comment,
    create_note,
    follow_user,
    get_note,
    like_note,
    list_comments,
    list_notes,
    unfollow_user,
    unlike_note,
)

router = APIRouter()


@router.post("/notes", response_model=BaseResponse)
async def create(
    data: NoteCreate = Body(...),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await create_note(db, user_id, data.title, data.content)
    return BaseResponse(success=True, data={"id": note.id, "title": note.title})


@router.get("/notes", response_model=BaseResponse)
async def list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await list_notes(db, page, size)
    return BaseResponse(success=True, data=result)


@router.get("/notes/{note_id}", response_model=BaseResponse)
async def detail(note_id: str, db: AsyncSession = Depends(get_db)):
    note = await get_note(db, note_id)
    return BaseResponse(success=True, data=note)


@router.get("/notes/{note_id}/comments", response_model=BaseResponse)
async def list_note_comments(note_id: str, db: AsyncSession = Depends(get_db)):
    comments = await list_comments(db, note_id)
    return BaseResponse(success=True, data=comments)


@router.post("/notes/{note_id}/like", response_model=BaseResponse)
async def like(
    note_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await like_note(db, note_id, user_id)
    return BaseResponse(success=True, data=result)


@router.post("/notes/{note_id}/unlike", response_model=BaseResponse)
async def unlike(
    note_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await unlike_note(db, note_id, user_id)
    return BaseResponse(success=True, data=result)


@router.post("/notes/{note_id}/comments", response_model=BaseResponse)
async def comment(
    note_id: str,
    content: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await add_comment(db, note_id, user_id, content)
    return BaseResponse(success=True, data=result)


@router.post("/follow/{target_id}", response_model=BaseResponse)
async def follow(
    target_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await follow_user(db, user_id, target_id)
    return BaseResponse(success=True, data=result)


@router.post("/unfollow/{target_id}", response_model=BaseResponse)
async def unfollow(
    target_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await unfollow_user(db, user_id, target_id)
    return BaseResponse(success=True, data=result)
