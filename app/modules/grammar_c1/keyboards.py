from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback

from .callbacks import GrammarActionCallback, GrammarListCallback, GrammarQuizCallback
from .schemas import GrammarTopic
from .service import option_order

OPTION_LABELS = ("A", "B", "C", "D")

def action(action: str, value: str = "0") -> str:
    return GrammarActionCallback(action=action, value=value).pack()

def build_course_home(*, has_active_attempt: bool, has_progress: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_active_attempt or has_progress:
        builder.button(text="▶️ Продолжить обучение", callback_data=action("continue"))
    builder.button(text="🚀 Начать с первой темы", callback_data=action("open", "1"))
    builder.button(text="🔴 Все темы C1", callback_data=GrammarListCallback(level="C1", page=0))
    builder.button(text="🎲 Случайная тема", callback_data=action("random"))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="🧹 Сбросить прогресс", callback_data=action("reset_request"))
    builder.button(text="← К уровням грамматики", callback_data=SectionCallback(name="grammar"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_topic_list(
    *,
    topics: tuple[GrammarTopic, ...],
    completed: set[int],
    mastered: set[int],
    level: str,
    page: int,
    page_size: int = 8,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * page_size
    page_topics = topics[start : start + page_size]

    for topic in page_topics:
        if topic.order in mastered:
            marker = "✅"
        elif topic.order in completed:
            marker = "☑️"
        else:
            marker = "▫️"
        builder.button(
            text=f"{marker} {topic.order}. {topic.title_ru}",
            callback_data=action("open", str(topic.order)),
        )

    nav_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="←",
                callback_data=GrammarListCallback(level=level, page=page - 1).pack(),
            )
        )
    if start + page_size < len(topics):
        nav_buttons.append(
            InlineKeyboardButton(
                text="→",
                callback_data=GrammarListCallback(level=level, page=page + 1).pack(),
            )
        )
    builder.adjust(1)
    if nav_buttons:
        builder.row(*nav_buttons)
    builder.row(
        InlineKeyboardButton(text="← В C1", callback_data=action("home")),
    )
    return builder.as_markup()

def build_topic_card(topic_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Выполнить 3 задания", callback_data=action("start_quiz", str(topic_order)))
    if topic_order > 1:
        builder.button(text="← Предыдущая", callback_data=action("open", str(topic_order - 1)))
    if topic_order < 70:
        builder.button(text="Следующая →", callback_data=action("open", str(topic_order + 1)))
    builder.button(text="📋 Список C1", callback_data=GrammarListCallback(level="C1", page=0))
    builder.button(text="← В C1", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()

def build_quiz_keyboard(*, attempt_id: int, topic: GrammarTopic, quiz_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    quiz = topic.quizzes[quiz_index]
    for display_index, option_index in enumerate(option_order(attempt_id, topic, quiz_index)):
        builder.button(
            text=OPTION_LABELS[display_index],
            callback_data=GrammarQuizCallback(
                attempt_id=attempt_id,
                topic_order=topic.order,
                quiz_index=quiz_index,
                option_index=option_index,
            ),
        )
    builder.adjust(2, 2)
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu").pack())
    )
    return builder.as_markup()

def build_quiz_feedback(attempt_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Следующее задание →", callback_data=action("next_quiz", str(attempt_id)))
    builder.button(text="💾 Сохранить и выйти", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_topic_result(topic_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить тему", callback_data=action("start_quiz", str(topic_order)))
    if topic_order < 70:
        builder.button(text="Следующая тема →", callback_data=action("open", str(topic_order + 1)))
    builder.button(text="📊 Мой прогресс", callback_data=action("progress"))
    builder.button(text="← В C1", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_progress_keyboard(current_topic_order: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Продолжить", callback_data=action("open", str(current_topic_order)))
    builder.button(text="← В C1", callback_data=action("home"))
    builder.button(text="🏠 Главное меню", callback_data=SectionCallback(name="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def build_reset_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, удалить прогресс", callback_data=action("reset_confirm"))
    builder.button(text="Отмена", callback_data=action("home"))
    builder.adjust(1)
    return builder.as_markup()
