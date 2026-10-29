from aiogram.filters.callback_data import CallbackData

class GrammarActionCallback(CallbackData, prefix="gbm"):
    action: str
    value: str

class GrammarListCallback(CallbackData, prefix="gbl"):
    level: str
    page: int

class GrammarQuizCallback(CallbackData, prefix="gbq"):
    attempt_id: int
    topic_order: int
    quiz_index: int
    option_index: int
