from aiogram.filters.callback_data import CallbackData

class CollocationActionCallback(CallbackData, prefix="cia"):
    action: str
    value: str

class CollocationListCallback(CallbackData, prefix="cil"):
    group_type: str
    group_value: str
    page: int

class CollocationQuizCallback(CallbackData, prefix="ciq"):
    attempt_id: int
    card_order: int
    option_index: int
