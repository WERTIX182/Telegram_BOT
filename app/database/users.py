from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def upsert_telegram_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    first_name: str,
    last_name: str | None,
    username: str | None,
) -> None:
    """Create the FK parent row and refresh public Telegram profile fields."""
    statement = insert(User).values(
        telegram_id=telegram_id,
        first_name=first_name or "Telegram user",
        last_name=last_name,
        username=username,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[User.telegram_id],
        set_={
            "first_name": statement.excluded.first_name,
            "last_name": statement.excluded.last_name,
            "username": statement.excluded.username,
        },
    )
    await session.execute(statement)
    await session.commit()

