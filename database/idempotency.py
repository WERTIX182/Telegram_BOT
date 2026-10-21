from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


ResultType = TypeVar("ResultType")


def idempotent_answer(result_type: type[ResultType]):
    """Convert a concurrent unique-key race into an ordinary rejected answer."""

    def decorate(function: Callable[..., Awaitable[ResultType]]):
        @wraps(function)
        async def wrapped(session: AsyncSession, *args: Any, **kwargs: Any) -> ResultType:
            try:
                return await function(session, *args, **kwargs)
            except IntegrityError:
                await session.rollback()
                return result_type(accepted=False)

        return wrapped

    return decorate

