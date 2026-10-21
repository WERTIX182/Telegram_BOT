from aiogram.filters.callback_data import CallbackData

class SectionCallback(CallbackData, prefix="section"):
    """
    Callback для навигации по разделам бота.
    name: идентификатор раздела (main_menu, level_test, grammar, verbs, ...)
    """
    name: str
