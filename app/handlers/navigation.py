from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.callbacks import SectionCallback
from app.learning import find_continue_target
from app.keyboards.main import get_main_menu_keyboard

# Импорты для модальных глаголов
from app.modules.modal_verbs.texts import COURSE_HOME_TEXT as MODAL_HOME_TEXT
from app.modules.modal_verbs.keyboards import build_course_home as build_modal_home
from app.modules.modal_verbs.repository import get_or_create_progress as get_modal_progress, get_active_attempt as get_modal_attempt
from app.modules.modal_verbs.service import parse_topic_set as parse_modal_set

# Импорты для глаголов C1
from app.modules.verbs_c1.texts import COURSE_HOME_TEXT as VERBS_C1_HOME_TEXT
from app.modules.verbs_c1.keyboards import build_course_home as build_verbs_c1_home
from app.modules.verbs_c1.repository import get_or_create_progress as get_verbs_c1_progress, get_active_attempt as get_verbs_c1_attempt
from app.modules.verbs_c1.service import parse_card_set as parse_verbs_c1_set

# Импорты для глаголов B1-B2
from app.modules.verbs_b1_b2.texts import COURSE_HOME_TEXT as VERBS_B1_B2_HOME_TEXT
from app.modules.verbs_b1_b2.keyboards import build_course_home as build_verbs_b1_b2_home
from app.modules.verbs_b1_b2.repository import get_or_create_progress as get_verbs_b1_b2_progress, get_active_attempt as get_verbs_b1_b2_attempt
from app.modules.verbs_b1_b2.service import parse_card_set as parse_verbs_b1_b2_set

# Импорты для глаголов A1-A2
from app.modules.verbs_a1_a2.texts import COURSE_HOME_TEXT as VERBS_A1_A2_HOME_TEXT
from app.modules.verbs_a1_a2.keyboards import build_course_home as build_verbs_a1_a2_home
from app.modules.verbs_a1_a2.repository import get_or_create_progress as get_verbs_a1_a2_progress, get_active_attempt as get_verbs_a1_a2_attempt
from app.modules.verbs_a1_a2.service import parse_card_set as parse_verbs_a1_a2_set

# Импорты для коллокаций Intermediate
from app.modules.collocations_intermediate.texts import COURSE_HOME_TEXT as COLLOCATIONS_HOME_TEXT
from app.modules.collocations_intermediate.keyboards import build_course_home as build_collocations_home
from app.modules.collocations_intermediate.repository import get_or_create_progress as get_collocations_progress, get_active_attempt as get_collocations_attempt
from app.modules.collocations_intermediate.service import parse_card_set as parse_collocations_set

# Импорты для фразовых глаголов Intermediate
from app.modules.phrasal_verbs_intermediate.texts import COURSE_HOME_TEXT as PHRASAL_VERBS_INT_HOME_TEXT
from app.modules.phrasal_verbs_intermediate.keyboards import build_course_home as build_phrasal_verbs_int_home
from app.modules.phrasal_verbs_intermediate.repository import get_or_create_progress as get_phrasal_verbs_int_progress, get_active_attempt as get_phrasal_verbs_int_attempt
from app.modules.phrasal_verbs_intermediate.service import parse_card_set as parse_phrasal_verbs_int_set

# Импорты для фразовых глаголов Advanced
from app.modules.phrasal_verbs_advanced.texts import COURSE_HOME_TEXT as PHRASAL_VERBS_ADV_HOME_TEXT
from app.modules.phrasal_verbs_advanced.keyboards import build_course_home as build_phrasal_verbs_adv_home
from app.modules.phrasal_verbs_advanced.repository import get_or_create_progress as get_phrasal_verbs_adv_progress, get_active_attempt as get_phrasal_verbs_adv_attempt
from app.modules.phrasal_verbs_advanced.service import parse_card_set as parse_phrasal_verbs_adv_set

# Импорты для идиом Intermediate
from app.modules.idioms_intermediate.texts import COURSE_HOME_TEXT as IDIOMS_INTERMEDIATE_HOME_TEXT
from app.modules.idioms_intermediate.keyboards import build_course_home as build_idioms_intermediate_home
from app.modules.idioms_intermediate.repository import get_or_create_progress as get_idioms_intermediate_progress, get_active_attempt as get_idioms_intermediate_attempt
from app.modules.idioms_intermediate.service import parse_card_set as parse_idioms_intermediate_set

# Импорты для идиом Advanced
from app.modules.idioms_advanced.texts import COURSE_HOME_TEXT as IDIOMS_ADVANCED_HOME_TEXT
from app.modules.idioms_advanced.keyboards import build_course_home as build_idioms_advanced_home
from app.modules.idioms_advanced.repository import get_or_create_progress as get_idioms_advanced_progress, get_active_attempt as get_idioms_advanced_attempt
from app.modules.idioms_advanced.service import parse_card_set as parse_idioms_advanced_set

router = Router(name="navigation")

# ---------- Безопасное редактирование сообщения ----------
async def _safe_edit(message: Message, text: str, reply_markup=None) -> None:
    """Редактирует сообщение, игнорируя ошибку 'message is not modified'."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise

# ---------- Клавиатура выбора раздела глаголов ----------
def get_verbs_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Глаголы A1–A2", callback_data=SectionCallback(name="verbs_a1_a2"))
    builder.button(text="🔴 Глаголы B1–B2", callback_data=SectionCallback(name="verbs_b1_b2"))
    builder.button(text="🔵 Глаголы C1", callback_data=SectionCallback(name="verbs_c1"))
    builder.button(text="🧭 Модальные глаголы", callback_data=SectionCallback(name="modal_verbs"))
    builder.button(text="🔀 Неправильные глаголы", callback_data=SectionCallback(name="irregular_verbs"))
    builder.button(text="🧩 Глагольные модели", callback_data=SectionCallback(name="verb_patterns"))
    builder.button(text="← В главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# ---------- Клавиатура выбора уровня коллокаций ----------
def get_collocations_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔗 Intermediate (B1–B2)",
        callback_data=SectionCallback(name="collocations_intermediate"),
    )
    builder.button(
        text="🔷 Advanced (C1)",
        callback_data=SectionCallback(name="collocations_advanced"),
    )
    builder.button(
        text="← В главное меню",
        callback_data=SectionCallback(name="main_menu"),
    )
    builder.adjust(1)
    return builder.as_markup()

# ---------- Клавиатура выбора уровня фразовых глаголов ----------
def get_phrasal_verbs_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Intermediate (B1–B2)", callback_data=SectionCallback(name="phrasal_verbs_int"))
    builder.button(text="🔹 Advanced (B2–C1)", callback_data=SectionCallback(name="phrasal_verbs_adv"))
    builder.button(text="← В главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# ---------- Клавиатура выбора уровня идиом ----------
def get_idioms_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Intermediate (B1–B2)", callback_data=SectionCallback(name="idioms_intermediate"))
    builder.button(text="🔹 Advanced (B2–C1)", callback_data=SectionCallback(name="idioms_advanced"))
    builder.button(text="← В главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

# ---------- Обработчики ----------
@router.callback_query(SectionCallback.filter(F.name == "main_menu"))
async def back_to_main_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await _safe_edit(
        callback.message,
        "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "verbs"))
async def verbs_choice(callback: CallbackQuery) -> None:
    """Меню выбора раздела глаголов."""
    await _safe_edit(
        callback.message,
        "🔤 <b>Раздел «Глаголы»</b>\n\n"
        "Выберите, какой раздел глаголов вы хотите изучать:",
        reply_markup=get_verbs_choice_keyboard()
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "phrasal_verbs"))
async def phrasal_verbs_choice(callback: CallbackQuery) -> None:
    """Меню выбора уровня фразовых глаголов."""
    await _safe_edit(
        callback.message,
        "🔁 <b>Фразовые глаголы</b>\n\n"
        "Выберите уровень:",
        reply_markup=get_phrasal_verbs_choice_keyboard()
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "idioms"))
async def idioms_choice(callback: CallbackQuery) -> None:
    """Меню выбора уровня идиом."""
    await _safe_edit(
        callback.message,
        "🎭 <b>Идиомы</b>\n\n"
        "Выберите уровень:",
        reply_markup=get_idioms_choice_keyboard()
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "idioms_intermediate"))
async def open_idioms_intermediate(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля идиом Intermediate."""
    async with session_factory() as session:
        progress = await get_idioms_intermediate_progress(session, callback.from_user.id)
        active = await get_idioms_intermediate_attempt(session, callback.from_user.id)
        completed = parse_idioms_intermediate_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        IDIOMS_INTERMEDIATE_HOME_TEXT,
        reply_markup=build_idioms_intermediate_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "idioms_advanced"))
async def open_idioms_advanced(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля идиом Advanced."""
    async with session_factory() as session:
        progress = await get_idioms_advanced_progress(session, callback.from_user.id)
        active = await get_idioms_advanced_attempt(session, callback.from_user.id)
        completed = parse_idioms_advanced_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        IDIOMS_ADVANCED_HOME_TEXT,
        reply_markup=build_idioms_advanced_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "modal_verbs"))
async def open_modal_verbs(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля модальных глаголов."""
    async with session_factory() as session:
        progress = await get_modal_progress(session, callback.from_user.id)
        active = await get_modal_attempt(session, callback.from_user.id)
        completed = parse_modal_set(progress.completed_topics_json)
    await _safe_edit(
        callback.message,
        MODAL_HOME_TEXT,
        reply_markup=build_modal_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "verbs_c1"))
async def open_verbs_c1(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля глаголов C1."""
    async with session_factory() as session:
        progress = await get_verbs_c1_progress(session, callback.from_user.id)
        active = await get_verbs_c1_attempt(session, callback.from_user.id)
        completed = parse_verbs_c1_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        VERBS_C1_HOME_TEXT,
        reply_markup=build_verbs_c1_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "verbs_b1_b2"))
async def open_verbs_b1_b2(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля глаголов B1-B2."""
    async with session_factory() as session:
        progress = await get_verbs_b1_b2_progress(session, callback.from_user.id)
        active = await get_verbs_b1_b2_attempt(session, callback.from_user.id)
        completed = parse_verbs_b1_b2_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        VERBS_B1_B2_HOME_TEXT,
        reply_markup=build_verbs_b1_b2_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "verbs_a1_a2"))
async def open_verbs_a1_a2(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля глаголов A1-A2."""
    async with session_factory() as session:
        progress = await get_verbs_a1_a2_progress(session, callback.from_user.id)
        active = await get_verbs_a1_a2_attempt(session, callback.from_user.id)
        completed = parse_verbs_a1_a2_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        VERBS_A1_A2_HOME_TEXT,
        reply_markup=build_verbs_a1_a2_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "collocations"))
async def collocations_choice(callback: CallbackQuery) -> None:
    """Показать выбор уровня коллокаций."""
    await _safe_edit(
        callback.message,
        "🔗 <b>Коллокации</b>\n\nВыберите уровень:",
        reply_markup=get_collocations_choice_keyboard(),
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "collocations_intermediate"))
async def open_collocations(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля коллокаций Intermediate."""
    async with session_factory() as session:
        progress = await get_collocations_progress(session, callback.from_user.id)
        active = await get_collocations_attempt(session, callback.from_user.id)
        completed = parse_collocations_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        COLLOCATIONS_HOME_TEXT,
        reply_markup=build_collocations_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "phrasal_verbs_int"))
async def open_phrasal_verbs_intermediate(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля фразовых глаголов Intermediate."""
    async with session_factory() as session:
        progress = await get_phrasal_verbs_int_progress(session, callback.from_user.id)
        active = await get_phrasal_verbs_int_attempt(session, callback.from_user.id)
        completed = parse_phrasal_verbs_int_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        PHRASAL_VERBS_INT_HOME_TEXT,
        reply_markup=build_phrasal_verbs_int_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

@router.callback_query(SectionCallback.filter(F.name == "phrasal_verbs_adv"))
async def open_phrasal_verbs_advanced(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Открыть главную страницу модуля фразовых глаголов Advanced."""
    async with session_factory() as session:
        progress = await get_phrasal_verbs_adv_progress(session, callback.from_user.id)
        active = await get_phrasal_verbs_adv_attempt(session, callback.from_user.id)
        completed = parse_phrasal_verbs_adv_set(progress.completed_cards_json)
    await _safe_edit(
        callback.message,
        PHRASAL_VERBS_ADV_HOME_TEXT,
        reply_markup=build_phrasal_verbs_adv_home(has_progress=bool(completed) or active is not None)
    )
    await callback.answer()

# ---------- Обработчик для кнопки "Продолжить обучение" ----------
@router.callback_query(SectionCallback.filter(F.name == "continue_learning"))
async def continue_learning(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Offer the most recently updated course with saved progress."""
    async with session_factory() as session:
        target = await find_continue_target(session, callback.from_user.id)
    if target is None:
        await callback.answer("Сохранённый прогресс пока не найден.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text=f"▶️ {target.label}", callback_data=target.callback_data)
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    await _safe_edit(
        callback.message,
        f"▶️ <b>Продолжить обучение</b>\n\nПоследний курс: {target.label}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()

# ---------- Заглушка для нереализованного раздела (тест на уровень удалён, так как модуль реализован) ----------
# Обработчик для level_test теперь находится в модуле level_test
