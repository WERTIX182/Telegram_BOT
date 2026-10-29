from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .users import upsert_telegram_user


class UserRegistrationMiddleware(BaseMiddleware):
    """Guarantee that every course progress row has a parent user row."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        factory: async_sessionmaker[AsyncSession] | None = data.get("session_factory")
        if user is not None and factory is not None:
            async with factory() as session:
                await upsert_telegram_user(
                    session,
                    telegram_id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                )
        return await handler(event, data)

