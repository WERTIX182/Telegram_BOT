from aiogram.filters.callback_data import CallbackData

class IdiomActionCallback(CallbackData, prefix="idia"):
    action: str
    value: str

class IdiomListCallback(CallbackData, prefix="idil"):
    group_type: str
    group_value: str
    page: int

class IdiomQuizCallback(CallbackData, prefix="idiq"):
    attempt_id: int
    card_order: int
    option_index: int
