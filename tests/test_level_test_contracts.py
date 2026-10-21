from __future__ import annotations

import unittest

from app.modules.level_test.content import LEVEL_ORDER, load_questions
from app.modules.level_test.service import (
    canonical_index_for_display,
    display_options,
    dump_layout,
    evaluate_level,
    load_layout,
    make_layout,
    question_at,
)


class LevelTestContractTests(unittest.TestCase):
    def test_layout_is_stable_serializable_and_complete(self) -> None:
        first = make_layout(seed=12345)
        same = make_layout(seed=12345)
        other = make_layout(seed=54321)
        self.assertEqual(first, same)
        self.assertNotEqual(first, other)
        self.assertEqual(20, len(first.question_ids))
        self.assertEqual(first, load_layout(*dump_layout(first)))
        for position in range(20):
            question = question_at(first, position)
            displayed = display_options(first, question)
            self.assertEqual(4, len(displayed))
            canonical = {
                canonical_index_for_display(first, question, display_index)
                for display_index in range(4)
            }
            self.assertEqual({0, 1, 2, 3}, canonical)

    def test_question_distribution_and_scoring_edges(self) -> None:
        questions = load_questions()
        self.assertEqual(20, len(questions))
        self.assertEqual(
            {level: 4 for level in LEVEL_ORDER},
            {level: sum(question.level == level for question in questions) for level in LEVEL_ORDER},
        )
        self.assertEqual("A1", evaluate_level([]).level)
        self.assertEqual("C1", evaluate_level(question.id for question in questions).level)
        self.assertTrue(evaluate_level(question.id for question in questions).ceiling_reached)
        c1_only = [question.id for question in questions if question.level == "C1"]
        self.assertEqual("A1", evaluate_level(c1_only).level)


if __name__ == "__main__":
    unittest.main()

