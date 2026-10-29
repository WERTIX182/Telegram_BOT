from aiogram.filters.callback_data import CallbackData

class ExtraPracticeActionCallback(CallbackData, prefix="cxpa"):
    action: str
    level_code: str
    card_order: int

class ExtraPracticeQuizCallback(CallbackData, prefix="cxpq"):
    attempt_id: int
    question_index: int
    option_index: int
