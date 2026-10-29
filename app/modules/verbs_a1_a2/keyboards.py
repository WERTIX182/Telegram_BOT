from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback

from .callbacks import VerbActionCallback, VerbListCallback, VerbQuizCallback
from .schemas import VerbCard
from .service import option_order

OPTION_LABELS = ("A", "B", "C", "D")

def action(action_name: str, value: str = "0") -> str:
    return VerbActionCallback(action=action_name, value=value).pack()

def build_course_home(*, has_progress: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_progress:
        builder.button(text="▶️ Продолжить обучение", callback_data=action("continue"))
    builder.button(text="🚀 Начать с первой карточки", callback_data=action("open", "1"))
    builder.button(text="🟢 Карточки A1", callback_data=VerbListCallback(level="A1", page=0))
    builder.button(text="🟡 Карточки A2", callback_data=VerbListCallback(level="A2", page=0))
    builder.button(text="🎲 Случайная карточка", callback_data=action("random"))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="🧹 Сбросить прогресс", callback_data=action("reset_request"))
    builder.button(text="← К разделам глаголов", callback_data=SectionCallback(name="verbs"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 1, 2, 1, 1, 1, 1, 1)
    return builder.as_markup()

def build_card_list(*, cards: tuple[VerbCard, ...], completed: set[int], mastered: set[int], level: str, page: int, page_size: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    page_cards = cards[start:start + page_size]
    for card in page_cards:
        marker = "✅" if card.order in mastered else "☑️" if card.order in completed else "▫️"
        builder.button(text=f"{marker} {card.order}. {card.title_en}", callback_data=action("open", str(card.order)))
    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="←", callback_data=VerbListCallback(level=level, page=page-1).pack()))
    if start + page_size < len(cards):
        nav.append(InlineKeyboardButton(text="→", callback_data=VerbListCallback(level=level, page=page+1).pack()))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="← В A1–A2", callback_data=action("home")))
    return builder.as_markup()

def build_card(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Мини-квиз", callback_data=action("start_quiz", str(card_order)))
    if card_order > 1:
        builder.button(text="← Предыдущая", callback_data=action("open", str(card_order-1)))
    if card_order < 50:
        builder.button(text="Следующая →", callback_data=action("open", str(card_order+1)))
    builder.button(text="📋 Список A1", callback_data=VerbListCallback(level="A1", page=0))
    builder.button(text="📋 Список A2", callback_data=VerbListCallback(level="A2", page=0))
    builder.button(text="← В A1–A2", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 2, 2, 1, 1)
    return builder.as_markup()

def build_quiz(attempt_id: int, card: VerbCard) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for display_index, option_index in enumerate(option_order(attempt_id, card)):
        builder.button(text=OPTION_LABELS[display_index], callback_data=VerbQuizCallback(attempt_id=attempt_id, card_order=card.order, option_index=option_index))
    builder.adjust(2, 2)
    builder.row(InlineKeyboardButton(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu").pack()))
    return builder.as_markup()

def build_result(card_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить карточку", callback_data=action("start_quiz", str(card_order)))
    if card_order < 50:
        builder.button(text="Следующая карточка →", callback_data=action("open", str(card_order+1)))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="← В A1–A2", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_progress(current_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Продолжить", callback_data=action("open", str(current_order)))
    builder.button(text="← В A1–A2", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_reset_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, удалить прогресс", callback_data=action("reset_confirm"))
    builder.button(text="Отмена", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()
