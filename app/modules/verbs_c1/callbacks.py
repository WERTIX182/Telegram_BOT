from aiogram.filters.callback_data import CallbackData

class VerbActionCallback(CallbackData, prefix="vca"):
    action: str
    value: str

class VerbListCallback(CallbackData, prefix="vcl"):
    level: str
    page: int

class VerbQuizCallback(CallbackData, prefix="vcq"):
    attempt_id: int
    card_order: int
    option_index: int
