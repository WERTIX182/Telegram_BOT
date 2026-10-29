from aiogram.filters.callback_data import CallbackData

class GrammarActionCallback(CallbackData, prefix="gcm"):
    action: str
    value: str

class GrammarListCallback(CallbackData, prefix="gcl"):
    level: str
    page: int

class GrammarQuizCallback(CallbackData, prefix="gcq"):
    attempt_id: int
    topic_order: int
    quiz_index: int
    option_index: int
