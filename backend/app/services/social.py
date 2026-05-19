import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.social import Note, NoteComment, NoteLike, UserFollow


async def get_note(db: AsyncSession, note_id: str) -> dict:
    note = await db.get(Note, note_id)
    if not note:
        raise NotFoundException()
    return {
        "id": note.id,
        "user_id": note.user_id,
        "title": note.title,
        "content": note.content,
        "likes_count": note.likes_count,
        "comments_count": note.comments_count,
        "created_at": str(note.created_at),
    }


async def list_comments(db: AsyncSession, note_id: str) -> list[dict]:
    result = await db.execute(
        select(NoteComment)
        .where(NoteComment.note_id == note_id)
        .order_by(NoteComment.created_at.asc())
    )
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "content": c.content,
            "created_at": str(c.created_at),
        }
        for c in result.scalars().all()
    ]


async def create_note(db: AsyncSession, user_id: str, title: str, content: str) -> Note:
    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def list_notes(db: AsyncSession, page: int = 1, size: int = 20) -> dict:
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


async def like_note(db: AsyncSession, note_id: str, user_id: str) -> dict:
    result = await db.execute(
        text(
            "INSERT INTO note_likes (id, note_id, user_id) VALUES (:id, :nid, :uid) "
            "ON CONFLICT (note_id, user_id) DO NOTHING"
        ),
        {"id": str(uuid.uuid4()), "nid": note_id, "uid": user_id},
    )
    if result.rowcount == 0:
        raise ConflictException("已点赞")
    await db.execute(
        Note.__table__.update().where(Note.id == note_id).values(likes_count=Note.likes_count + 1)
    )
    await db.commit()
    return {"status": "liked"}


async def unlike_note(db: AsyncSession, note_id: str, user_id: str) -> dict:
    result = await db.execute(
        select(NoteLike).where(NoteLike.note_id == note_id, NoteLike.user_id == user_id)
    )
    like = result.scalar_one_or_none()
    if not like:
        raise NotFoundException()
    await db.delete(like)
    await db.execute(
        Note.__table__.update().where(Note.id == note_id).values(likes_count=Note.likes_count - 1)
    )
    await db.commit()
    return {"status": "unliked"}


async def add_comment(db: AsyncSession, note_id: str, user_id: str, content: str) -> dict:
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


async def follow_user(db: AsyncSession, user_id: str, target_id: str) -> dict:
    if user_id == target_id:
        raise BadRequestException("不能关注自己")
    result = await db.execute(
        text(
            "INSERT INTO user_follows (id, follower_id, following_id) VALUES (:id, :fid, :tid) "
            "ON CONFLICT (follower_id, following_id) DO NOTHING"
        ),
        {"id": str(uuid.uuid4()), "fid": user_id, "tid": target_id},
    )
    if result.rowcount == 0:
        raise ConflictException("已关注")
    await db.commit()
    return {"status": "followed"}


async def unfollow_user(db: AsyncSession, user_id: str, target_id: str) -> dict:
    result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == user_id, UserFollow.following_id == target_id
        )
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise NotFoundException()
    await db.delete(follow)
    await db.commit()
    return {"status": "unfollowed"}
