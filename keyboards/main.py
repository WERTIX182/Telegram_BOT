from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import SectionCallback
from app.modules.level_test import level_test_entry_callback

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню."""
    builder = InlineKeyboardBuilder()

    # Используем прямой callback для теста на уровень
    builder.button(text="📝 Тест на уровень", callback_data=level_test_entry_callback())
    builder.button(text="📚 Грамматика", callback_data=SectionCallback(name="grammar"))
    builder.button(text="🔤 Глаголы", callback_data=SectionCallback(name="verbs"))
    builder.button(text="🔗 Коллокации", callback_data=SectionCallback(name="collocations"))
    builder.button(text="🔁 Фразовые глаголы", callback_data=SectionCallback(name="phrasal_verbs"))
    builder.button(text="🎭 Идиомы", callback_data=SectionCallback(name="idioms"))
    builder.button(text="🧩 Словообразование", callback_data=SectionCallback(name="word_formation"))

    builder.button(text="▶️ Продолжить обучение", callback_data=SectionCallback(name="continue_learning"))

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()
