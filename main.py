from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent

from app.config import config
from app.database.engine import create_tables, engine, session_factory
from app.database.middleware import UserRegistrationMiddleware
from app.handlers import main_menu_router, navigation_router
from app.modules.collocations_advanced import router as collocations_advanced_router
from app.modules.collocations_extra_quizzes import router as collocations_extra_router
from app.modules.collocations_intermediate import router as collocations_intermediate_router
from app.modules.grammar_a1_a2 import router as grammar_a1_a2_router
from app.modules.grammar_b1_b2 import router as grammar_b1_b2_router
from app.modules.grammar_c1 import router as grammar_c1_router
from app.modules.idioms_advanced import router as idioms_advanced_router
from app.modules.idioms_extra_quizzes import router as idioms_extra_router
from app.modules.idioms_intermediate import router as idioms_intermediate_router
from app.modules.irregular_verbs import router as irregular_verbs_router
from app.modules.level_test import router as level_test_router
from app.modules.modal_verbs import router as modal_verbs_router
from app.modules.phrasal_verbs_advanced import router as phrasal_verbs_advanced_router
from app.modules.phrasal_verbs_extra_quizzes import router as pv_extra_router
from app.modules.phrasal_verbs_intermediate import router as phrasal_verbs_intermediate_router
from app.modules.verb_patterns import router as verb_patterns_router
from app.modules.verbs_a1_a2 import router as verbs_a1_a2_router
from app.modules.verbs_b1_b2 import router as verbs_b1_b2_router
from app.modules.verbs_c1 import router as verbs_c1_router
from app.modules.word_formation import router as word_formation_router


logger = logging.getLogger(__name__)


COURSE_ROUTERS = (
    collocations_extra_router,
    idioms_extra_router,
    pv_extra_router,
    level_test_router,
    word_formation_router,
    modal_verbs_router,
    verbs_c1_router,
    verbs_b1_b2_router,
    verbs_a1_a2_router,
    irregular_verbs_router,
    verb_patterns_router,
    phrasal_verbs_intermediate_router,
    phrasal_verbs_advanced_router,
    collocations_intermediate_router,
    collocations_advanced_router,
    idioms_intermediate_router,
    idioms_advanced_router,
    grammar_a1_a2_router,
    grammar_b1_b2_router,
    grammar_c1_router,
)


def create_dispatcher() -> Dispatcher:
    """Build the dispatcher without starting Telegram polling.

    Keeping construction separate makes router registration testable offline.
    Specific course routers must remain before generic navigation handlers.
    """
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(UserRegistrationMiddleware())
    for router in COURSE_ROUTERS:
        dispatcher.include_router(router)
    dispatcher.include_router(main_menu_router)
    dispatcher.include_router(navigation_router)

    @dispatcher.errors()
    async def handle_unexpected_error(event: ErrorEvent) -> bool:
        exception = event.exception
        logger.error(
            "Unhandled update error: %s",
            type(exception).__name__,
            exc_info=(type(exception), exception, exception.__traceback__),
        )
        callback = event.update.callback_query
        if callback is not None:
            try:
                await callback.answer(
                    "Не удалось выполнить действие. Попробуйте ещё раз.",
                    show_alert=True,
                )
            except TelegramAPIError:
                logger.warning("Could not answer failed callback", exc_info=True)
        return True

    return dispatcher


async def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")

    await create_tables()
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher()

    logger.info("Бот запущен")
    try:
        await dispatcher.start_polling(
            bot,
            session_factory=session_factory,
            close_bot_session=False,
        )
    finally:
        await bot.session.close()
        await engine.dispose()

