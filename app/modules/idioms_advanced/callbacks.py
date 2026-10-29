from aiogram.filters.callback_data import CallbackData

class IdiomActionCallback(CallbackData, prefix="idaa"):
    action: str
    value: str

class IdiomListCallback(CallbackData, prefix="idal"):
    group_type: str
    group_value: str
    page: int

class IdiomQuizCallback(CallbackData, prefix="idaq"):
    attempt_id: int
    card_order: int
    option_index: int
