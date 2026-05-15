from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.social import Note, NoteComment, NoteLike, UserFollow

router = APIRouter()


@router.post("/notes")
async def create_note(
    title: str,
    content: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return {"id": note.id, "title": note.title}


@router.get("/notes")
async def list_notes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Note).order_by(Note.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    notes = result.scalars().all()
    count = await db.execute(select(func.count(Note.id)))
    return {
        "items": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "content": n.content,
                "likes_count": n.likes_count,
                "comments_count": n.comments_count,
                "created_at": str(n.created_at),
            }
            for n in notes
        ],
        "total": count.scalar(),
    }


@router.post("/notes/{note_id}/like")
async def like_note(
    note_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NoteLike).where(NoteLike.note_id == note_id, NoteLike.user_id == user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已点赞")
    db.add(NoteLike(note_id=note_id, user_id=user_id))
    await db.execute(
        Note.__table__.update().where(Note.id == note_id).values(likes_count=Note.likes_count + 1)
    )
    await db.commit()
    return {"status": "liked"}


@router.post("/notes/{note_id}/unlike")
async def unlike_note(
    note_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NoteLike).where(NoteLike.note_id == note_id, NoteLike.user_id == user_id)
    )
    like = result.scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.delete(like)
    await db.execute(
        Note.__table__.update().where(Note.id == note_id).values(likes_count=Note.likes_count - 1)
    )
    await db.commit()
    return {"status": "unliked"}


@router.post("/notes/{note_id}/comments")
async def add_comment(
    note_id: str,
    content: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = NoteComment(note_id=note_id, user_id=user_id, content=content)
    db.add(comment)
    await db.execute(
        Note.__table__.update()
        .where(Note.id == note_id)
        .values(comments_count=Note.comments_count + 1)
    )
    await db.commit()
    await db.refresh(comment)
    return {"id": comment.id, "content": comment.content}


@router.post("/follow/{target_id}")
async def follow_user(
    target_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id == target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == user_id, UserFollow.following_id == target_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)
    db.add(UserFollow(follower_id=user_id, following_id=target_id))
    await db.commit()
    return {"status": "followed"}


@router.post("/unfollow/{target_id}")
async def unfollow_user(
    target_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == user_id, UserFollow.following_id == target_id
        )
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.delete(follow)
    await db.commit()
    return {"status": "unfollowed"}
