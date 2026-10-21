from __future__ import annotations

import importlib
import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ContentCase:
    module: str
    loader: str
    expected_items: int
    quizzes_per_item: int


CONTENT_CASES = (
    ContentCase("level_test", "load_questions", 20, 1),
    ContentCase("grammar_a1_a2", "load_topics", 70, 3),
    ContentCase("grammar_b1_b2", "load_topics", 70, 3),
    ContentCase("grammar_c1", "load_topics", 70, 3),
    ContentCase("verbs_a1_a2", "load_cards", 50, 1),
    ContentCase("verbs_b1_b2", "load_cards", 50, 1),
    ContentCase("verbs_c1", "load_cards", 40, 1),
    ContentCase("irregular_verbs", "load_cards", 100, 1),
    ContentCase("verb_patterns", "load_topics", 35, 2),
    ContentCase("modal_verbs", "load_topics", 25, 2),
    ContentCase("collocations_intermediate", "load_cards", 54, 1),
    ContentCase("collocations_advanced", "load_cards", 54, 1),
    ContentCase("phrasal_verbs_intermediate", "load_cards", 56, 1),
    ContentCase("phrasal_verbs_advanced", "load_cards", 56, 1),
    ContentCase("idioms_intermediate", "load_cards", 56, 1),
    ContentCase("idioms_advanced", "load_cards", 56, 1),
    ContentCase("word_formation", "load_cards", 56, 1),
    ContentCase("idioms_extra_quizzes", "load_sets", 112, 2),
    ContentCase("phrasal_verbs_extra_quizzes", "load_sets", 112, 2),
    ContentCase("collocations_extra_quizzes", "load_sets", 108, 2),
)


def _identity(item: object) -> str:
    for attribute in ("id", "topic_id", "card_id", "question_id"):
        value = getattr(item, attribute, None)
        if value is not None:
            return str(value)
    level_code = getattr(item, "level_code", None)
    card_order = getattr(item, "card_order", None)
    if level_code is not None and card_order is not None:
        return f"{level_code}:{card_order}"
    order = getattr(item, "order", None)
    if order is not None:
        return str(order)
    raise AssertionError(f"Cannot determine identity for {item!r}")


def _quizzes(item: object) -> tuple[object, ...]:
    quizzes = getattr(item, "quizzes", None)
    if quizzes is not None:
        return tuple(quizzes)
    questions = getattr(item, "questions", None)
    if questions is not None:
        return tuple(questions)
    quiz = getattr(item, "quiz", None)
    if quiz is not None:
        return (quiz,)
    if hasattr(item, "options") and hasattr(item, "correct_index"):
        return (item,)
    raise AssertionError(f"Cannot find quizzes for {item!r}")


class JsonContractTests(unittest.TestCase):
    def test_every_json_file_is_valid(self) -> None:
        paths = sorted((PROJECT_ROOT / "app").rglob("*.json"))
        self.assertGreaterEqual(len(paths), 37)
        failures: list[str] = []
        for path in paths:
            try:
                with path.open("r", encoding="utf-8") as source:
                    json.load(source)
            except (OSError, json.JSONDecodeError) as error:
                failures.append(f"{path.relative_to(PROJECT_ROOT)}: {error}")
        self.assertEqual([], failures, "Invalid JSON files:\n" + "\n".join(failures))


class ContentContractTests(unittest.TestCase):
    def test_all_expected_modules_load_and_validate(self) -> None:
        failures: list[str] = []
        for case in CONTENT_CASES:
            with self.subTest(module=case.module):
                try:
                    content = importlib.import_module(f"app.modules.{case.module}.content")
                    loader: Callable[[], Iterable[object]] = getattr(content, case.loader)
                    items = tuple(loader())
                    self.assertEqual(case.expected_items, len(items))
                    identities = [_identity(item) for item in items]
                    self.assertEqual(len(identities), len(set(identities)), "duplicate item IDs")
                    for item in items:
                        quizzes = _quizzes(item)
                        self.assertEqual(case.quizzes_per_item, len(quizzes), _identity(item))
                        for quiz in quizzes:
                            options = tuple(getattr(quiz, "options"))
                            correct_index = int(getattr(quiz, "correct_index"))
                            self.assertGreaterEqual(len(options), 3)
                            self.assertEqual(len(options), len(set(options)), _identity(item))
                            self.assertIn(correct_index, range(len(options)), _identity(item))
                except Exception as error:  # aggregate all broken modules in one run
                    failures.append(f"{case.module}: {type(error).__name__}: {error}")
        self.assertEqual([], failures, "Broken content modules:\n" + "\n".join(failures))

    def test_extra_quizzes_match_every_base_card(self) -> None:
        families = (
            (
                "collocations",
                ("collocations_intermediate", "collocations_advanced"),
                "collocations_extra_quizzes",
            ),
            (
                "phrasal_verbs",
                ("phrasal_verbs_intermediate", "phrasal_verbs_advanced"),
                "phrasal_verbs_extra_quizzes",
            ),
            (
                "idioms",
                ("idioms_intermediate", "idioms_advanced"),
                "idioms_extra_quizzes",
            ),
        )
        for family, base_modules, extra_module in families:
            with self.subTest(family=family):
                base_ids: set[str] = set()
                for module_name in base_modules:
                    content = importlib.import_module(f"app.modules.{module_name}.content")
                    base_ids.update(_identity(item) for item in content.load_cards())
                extra_content = importlib.import_module(f"app.modules.{extra_module}.content")
                sets = tuple(extra_content.load_sets())
                source_ids = {str(item.base_card_id) for item in sets}
                self.assertEqual(base_ids, source_ids)
                self.assertTrue(all(len(item.questions) == 2 for item in sets))


if __name__ == "__main__":
    unittest.main()
