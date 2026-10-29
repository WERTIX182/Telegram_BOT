from __future__ import annotations

from html import escape
import json

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.callbacks import SectionCallback

from .callbacks import LevelPlacementActionCallback, LevelPlacementAnswerCallback
from .keyboards import OPTION_LABELS, build_home, build_question, build_result
from .repository import (
    create_attempt,
    get_active_attempt,
    get_attempt_for_user,
    get_latest_completed_attempt,
    record_answer,
)
from .service import (
    band_profile_text,
    display_options,
    load_layout,
    question_at,
    result_description,
)
from .texts import INTRO_TEXT, RESULT_LIMITATION

router = Router(name=__name__)

async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

def _render_question(attempt, position: int) -> str:
    layout = load_layout(attempt.question_order_json, attempt.option_orders_json)
    question = question_at(layout, position)
    shown_options = display_options(layout, question)
    options_text = "\n".join(
        f"<b>{OPTION_LABELS[index]})</b> {escape(option)}"
        for index, option in enumerate(shown_options)
    )
    return (
        f"<b>🧭 Вопрос {position + 1} из {len(layout.question_ids)}</b>\n\n"
        f"{escape(question.instruction)}\n\n"
        f"<b>{escape(question.prompt)}</b>\n\n"
        f"{options_text}\n\n"
        "Нажмите букву выбранного ответа."
    )

async def _show_question(message: Message, attempt, position: int) -> None:
    await _safe_edit(
        message,
        _render_question(attempt, position),
        reply_markup=build_question(attempt_id=attempt.id, position=position),
    )

def _result_text_from_values(
    *,
    level: str,
    score: int,
    band_scores: dict[str, int],
    is_borderline: bool,
    recommended_start_level: str,
    recommendation: str,
    ceiling_reached: bool = False,
) -> str:
    confidence_text = (
        "⚖️ Результат пограничный, поэтому старт рекомендован немного ниже для надёжного повторения."
        if is_borderline
        else "✅ Результат выглядит достаточно устойчивым внутри этого экспресс-теста."
    )
    ceiling_text = (
        "\n\n🔝 Вы достигли верхней границы теста. Он не различает C1 и C2."
        if ceiling_reached
        else ""
    )
    return (
        "<b>✅ Тест завершён</b>\n\n"
        f"Предварительный уровень: <b>{level}</b>\n"
        f"Результат: <b>{score} из 20</b>\n"
        f"Профиль по диапазонам: {band_profile_text(band_scores)}\n\n"
        f"{escape(result_description(level))}\n\n"
        f"{confidence_text}\n\n"
        f"Рекомендованный старт: <b>{recommended_start_level}</b>\n"
        f"{escape(recommendation)}"
        f"{ceiling_text}\n\n"
        f"{RESULT_LIMITATION}"
    )

async def _open_home(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        active = await get_active_attempt(session, callback.from_user.id)
        completed = await get_latest_completed_attempt(session, callback.from_user.id)
    await _safe_edit(
        callback.message,
        INTRO_TEXT,
        reply_markup=build_home(
            has_active=active is not None,
            has_completed=completed is not None,
        ),
    )
    await callback.answer()

@router.callback_query(LevelPlacementActionCallback.filter(F.action == "home"))
async def open_home_direct(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _open_home(callback, session_factory)

@router.callback_query(SectionCallback.filter(F.name == "level_test"))
async def open_home_legacy(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _open_home(callback, session_factory)

@router.callback_query(LevelPlacementActionCallback.filter(F.action.in_({"start", "restart"})))
async def start_test(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        attempt = await create_attempt(session, callback.from_user.id)
    await _show_question(callback.message, attempt, 0)
    await callback.answer("Тест начат")

@router.callback_query(LevelPlacementActionCallback.filter(F.action == "continue"))
async def continue_test(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        attempt = await get_active_attempt(session, callback.from_user.id)
    if attempt is None:
        await callback.answer("Незавершённый тест не найден", show_alert=True)
        return
    await _show_question(callback.message, attempt, attempt.current_position)
    await callback.answer()

@router.callback_query(LevelPlacementAnswerCallback.filter())
async def answer_question(
    callback: CallbackQuery,
    callback_data: LevelPlacementAnswerCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    async with session_factory() as session:
        outcome = await record_answer(
            session,
            attempt_id=callback_data.attempt_id,
            user_id=callback.from_user.id,
            position=callback_data.position,
            display_option=callback_data.display_option,
        )
        attempt = await get_attempt_for_user(
            session,
            callback_data.attempt_id,
            callback.from_user.id,
        )

    if attempt is None:
        await callback.answer("Попытка не найдена", show_alert=True)
        return
    if not outcome.accepted:
        if attempt.status == "in_progress":
            await _show_question(callback.message, attempt, attempt.current_position)
        await callback.answer("Этот ответ уже обработан")
        return
    if outcome.result is None:
        await _show_question(callback.message, attempt, outcome.next_position or 0)
        await callback.answer()
        return

    result = outcome.result
    await _safe_edit(
        callback.message,
        _result_text_from_values(
            level=result.level,
            score=result.score,
            band_scores=result.band_scores,
            is_borderline=result.is_borderline,
            recommended_start_level=result.recommended_start_level,
            recommendation=result.recommendation,
            ceiling_reached=result.ceiling_reached,
        ),
        reply_markup=build_result(),
    )
    await callback.answer("Готово")

@router.callback_query(LevelPlacementActionCallback.filter(F.action == "last_result"))
async def show_last_result(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    async with session_factory() as session:
        attempt = await get_latest_completed_attempt(session, callback.from_user.id)
    if attempt is None or attempt.result_level is None or attempt.result_score is None:
        await callback.answer("Сохранённый результат не найден", show_alert=True)
        return
    band_scores = json.loads(attempt.band_scores_json or "{}")
    recommendation = {
        "A1": "Начните с базовых тем A1.",
        "A2": "Начните с блока A2 после короткого повторения A1.",
        "B1": "Начните с блока B1.",
        "B2": "Начните с блока B2.",
        "C1": "Начните с раздела C1.",
    }[attempt.recommended_start_level or attempt.result_level]
    await _safe_edit(
        callback.message,
        _result_text_from_values(
            level=attempt.result_level,
            score=attempt.result_score,
            band_scores=band_scores,
            is_borderline=bool(attempt.result_is_borderline),
            recommended_start_level=attempt.recommended_start_level or attempt.result_level,
            recommendation=recommendation,
        ),
        reply_markup=build_result(),
    )
    await callback.answer()
