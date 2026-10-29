from aiogram.filters.callback_data import CallbackData


class VerbPatternActionCallback(CallbackData, prefix="vpa"):
    action: str
    value: str


class VerbPatternListCallback(CallbackData, prefix="vpl"):
    group_type: str
    group_value: str
    page: int


class VerbPatternQuizCallback(CallbackData, prefix="vpq"):
    attempt_id: int
    topic_order: int
    quiz_index: int
    option_index: int
