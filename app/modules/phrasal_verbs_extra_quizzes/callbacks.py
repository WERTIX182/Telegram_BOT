from aiogram.filters.callback_data import CallbackData


class ExtraPracticeActionCallback(CallbackData, prefix="pxpa"):
    action: str
    level_code: str
    card_order: int


class ExtraPracticeQuizCallback(CallbackData, prefix="pxpq"):
    attempt_id: int
    question_index: int
    option_index: int