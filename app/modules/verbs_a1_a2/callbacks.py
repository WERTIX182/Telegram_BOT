from aiogram.filters.callback_data import CallbackData

class VerbActionCallback(CallbackData, prefix="vba"):
    action: str
    value: str

class VerbListCallback(CallbackData, prefix="vbl"):
    level: str
    page: int

class VerbQuizCallback(CallbackData, prefix="vbq"):
    attempt_id: int
    card_order: int
    option_index: int
