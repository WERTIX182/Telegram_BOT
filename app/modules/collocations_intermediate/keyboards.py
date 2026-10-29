from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.modules.collocations_extra_quizzes.integration import extra_practice_callback
from app.callbacks import SectionCallback

from .callbacks import CollocationActionCallback, CollocationListCallback, CollocationQuizCallback
from .content import TOTAL_CARDS
from .schemas import CollocationCard
from .service import option_order
from .texts import CATEGORY_NAMES

OPTION_LABELS = ("A", "B", "C", "D")

def action(action_name: str, value: str = "0") -> str:
    return CollocationActionCallback(action=action_name, value=value).pack()

def build_course_home(*, has_progress: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_progress:
        builder.button(text="▶️ Продолжить обучение", callback_data=action("continue"))
    builder.button(text="🚀 Начать с первой карточки", callback_data=action("open", "1"))
    builder.button(text="🗂 Выбрать тему", callback_data=action("categories"))
    builder.button(text="📋 Все 54 коллокации", callback_data=CollocationListCallback(group_type="all", group_value="ALL", page=0))
    builder.button(text="🎲 Случайная карточка", callback_data=action("random"))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="🧹 Сбросить прогресс", callback_data=action("reset_request"))
    builder.button(text="← К уровням коллокаций", callback_data=SectionCallback(name="collocations"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_categories() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category, label in CATEGORY_NAMES.items():
        builder.button(text=label, callback_data=CollocationListCallback(group_type="category", group_value=category, page=0))
    builder.button(text="← В Intermediate", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()

def build_card_list(*, cards: tuple[CollocationCard, ...], completed: set[int], mastered: set[int],
                    group_type: str, group_value: str, page: int, page_size: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    for card in cards[start:start + page_size]:
        marker = "✅" if card.order in mastered else "☑️" if card.order in completed else "▫️"
        builder.button(text=f"{marker} {card.order}. {card.phrase}", callback_data=action("open", str(card.order)))
    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="←", callback_data=CollocationListCallback(
            group_type=group_type, group_value=group_value, page=page-1).pack()))
    if start + page_size < len(cards):
        nav.append(InlineKeyboardButton(text="→", callback_data=CollocationListCallback(
            group_type=group_type, group_value=group_value, page=page+1).pack()))
    if nav:
        builder.row(*nav)
    back = action("categories") if group_type == "category" else action("home")
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=back))
    return builder.as_markup()

def build_card(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Мини-квиз", callback_data=action("start_quiz", str(card_order)))
    if card_order > 1:
        builder.button(text="← Предыдущая", callback_data=action("open", str(card_order-1)))
    if card_order < TOTAL_CARDS:
        builder.button(text="Следующая →", callback_data=action("open", str(card_order+1)))
    builder.button(text="📋 Карточки этой темы", callback_data=action("category_list", str(card_order)))
    builder.button(text="← В Intermediate", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()

def build_quiz(attempt_id: int, card: CollocationCard) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_index, canonical_index in enumerate(option_order(attempt_id, card)):
        builder.button(text=OPTION_LABELS[display_index], callback_data=CollocationQuizCallback(
            attempt_id=attempt_id, card_order=card.order, option_index=canonical_index))
    builder.adjust(2, 2)
    builder.row(InlineKeyboardButton(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu").pack()))
    return builder.as_markup()

def build_result(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить квиз", callback_data=action("start_quiz", str(card_order)))
    builder.button(
        text="🧠 Ещё 2 вопроса",
        callback_data=extra_practice_callback("i", card_order),
    )
    if card_order < TOTAL_CARDS:
        builder.button(text="Следующая карточка →", callback_data=action("open", str(card_order + 1)))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="← В Intermediate", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_progress(current_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Продолжить", callback_data=action("open", str(current_order)))
    builder.button(text="← В Intermediate", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_reset_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, удалить прогресс", callback_data=action("reset_confirm"))
    builder.button(text="Отмена", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()
