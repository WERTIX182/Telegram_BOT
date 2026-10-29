from aiogram.filters.callback_data import CallbackData

class GrammarActionCallback(CallbackData, prefix="gra"):
    action: str
    value: str

class GrammarListCallback(CallbackData, prefix="grl"):
    level: str
    page: int

class GrammarQuizCallback(CallbackData, prefix="grq"):
    attempt_id: int
    topic_order: int
    quiz_index: int
    option_index: int
