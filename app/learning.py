from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.collocations_advanced.callbacks import (
    CollocationActionCallback as AdvancedCollocationAction,
)
from app.modules.collocations_intermediate.callbacks import (
    CollocationActionCallback as IntermediateCollocationAction,
)
from app.modules.grammar_a1_a2.callbacks import GrammarActionCallback as GrammarA1A2Action
from app.modules.grammar_b1_b2.callbacks import GrammarActionCallback as GrammarB1B2Action
from app.modules.grammar_c1.callbacks import GrammarActionCallback as GrammarC1Action
from app.modules.idioms_advanced.callbacks import IdiomActionCallback as AdvancedIdiomAction
from app.modules.idioms_intermediate.callbacks import IdiomActionCallback as IntermediateIdiomAction
from app.modules.irregular_verbs.callbacks import IrregularVerbActionCallback
from app.modules.modal_verbs.callbacks import ModalVerbActionCallback
from app.modules.phrasal_verbs_advanced.callbacks import (
    PhrasalVerbActionCallback as AdvancedPhrasalVerbAction,
)
from app.modules.phrasal_verbs_intermediate.callbacks import (
    PhrasalVerbActionCallback as IntermediatePhrasalVerbAction,
)
from app.modules.verb_patterns.callbacks import VerbPatternActionCallback
from app.modules.verbs_a1_a2.callbacks import VerbActionCallback as VerbsA1A2Action
from app.modules.verbs_b1_b2.callbacks import VerbActionCallback as VerbsB1B2Action
from app.modules.verbs_c1.callbacks import VerbActionCallback as VerbsC1Action
from app.modules.word_formation.callbacks import WordFormationActionCallback


@dataclass(frozen=True)
class ContinueTarget:
    progress_table: str
    label: str
    callback_data: str


CONTINUE_TARGETS = (
    ContinueTarget("grammar_progress", "Грамматика A1–A2", GrammarA1A2Action(action="continue", value="0").pack()),
    ContinueTarget("grammar_b1_b2_progress", "Грамматика B1–B2", GrammarB1B2Action(action="continue", value="0").pack()),
    ContinueTarget("grammar_c1_progress", "Грамматика C1", GrammarC1Action(action="continue", value="0").pack()),
    ContinueTarget("verbs_a1_a2_progress", "Глаголы A1–A2", VerbsA1A2Action(action="continue", value="0").pack()),
    ContinueTarget("verbs_b1_b2_progress", "Глаголы B1–B2", VerbsB1B2Action(action="continue", value="0").pack()),
    ContinueTarget("verbs_c1_progress", "Глаголы C1", VerbsC1Action(action="continue", value="0").pack()),
    ContinueTarget("irregular_verb_progress", "Неправильные глаголы", IrregularVerbActionCallback(action="continue", value="0").pack()),
    ContinueTarget("verb_pattern_progress", "Глагольные модели", VerbPatternActionCallback(action="continue", value="0").pack()),
    ContinueTarget("modal_verb_progress", "Модальные глаголы", ModalVerbActionCallback(action="continue", value="0").pack()),
    ContinueTarget("collocation_intermediate_progress", "Коллокации Intermediate", IntermediateCollocationAction(action="continue", value="0").pack()),
    ContinueTarget("collocation_advanced_progress", "Коллокации Advanced", AdvancedCollocationAction(action="continue", value="0").pack()),
    ContinueTarget("phrasal_verb_intermediate_progress", "Фразовые глаголы Intermediate", IntermediatePhrasalVerbAction(action="continue", value="0").pack()),
    ContinueTarget("phrasal_verb_advanced_progress", "Фразовые глаголы Advanced", AdvancedPhrasalVerbAction(action="continue", value="0").pack()),
    ContinueTarget("idiom_intermediate_progress", "Идиомы Intermediate", IntermediateIdiomAction(action="continue", value="0").pack()),
    ContinueTarget("idiom_advanced_progress", "Идиомы Advanced", AdvancedIdiomAction(action="continue", value="0").pack()),
    ContinueTarget("word_formation_progress", "Словообразование", WordFormationActionCallback(action="continue", value="0").pack()),
)


async def find_continue_target(
    session: AsyncSession,
    user_id: int,
) -> ContinueTarget | None:
    latest: tuple[str, ContinueTarget] | None = None
    for target in CONTINUE_TARGETS:
        timestamp = await session.scalar(
            text(
                f'SELECT MAX(updated_at) FROM "{target.progress_table}" '
                "WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        )
        if timestamp is None:
            continue
        candidate = (str(timestamp), target)
        if latest is None or candidate[0] > latest[0]:
            latest = candidate
    return latest[1] if latest is not None else None

