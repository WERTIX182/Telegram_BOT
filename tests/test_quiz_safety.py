from __future__ import annotations

import importlib
import unittest

from app.quiz_utils import stable_option_order


class ShuffleContractTests(unittest.TestCase):
    def test_shared_shuffle_is_stable_and_varies_between_attempts(self) -> None:
        first = stable_option_order(
            attempt_id=42,
            item_id="sample",
            question_index=0,
            option_count=4,
        )
        self.assertEqual(
            first,
            stable_option_order(
                attempt_id=42,
                item_id="sample",
                question_index=0,
                option_count=4,
            ),
        )
        orders = {
            stable_option_order(
                attempt_id=attempt_id,
                item_id="sample",
                question_index=0,
                option_count=4,
            )
            for attempt_id in range(1, 21)
        }
        self.assertGreater(len(orders), 1)
        self.assertTrue(all(sorted(order) == [0, 1, 2, 3] for order in orders))

    def test_grammar_and_verbs_use_stable_canonical_orders(self) -> None:
        grammar_modules = ("grammar_a1_a2", "grammar_b1_b2", "grammar_c1")
        for module_name in grammar_modules:
            with self.subTest(module=module_name):
                content = importlib.import_module(f"app.modules.{module_name}.content")
                service = importlib.import_module(f"app.modules.{module_name}.service")
                topic = content.load_topics()[0]
                order = service.option_order(77, topic, 0)
                self.assertEqual(order, service.option_order(77, topic, 0))
                self.assertEqual(list(range(len(topic.quizzes[0].options))), sorted(order))

        verb_modules = ("verbs_a1_a2", "verbs_b1_b2", "verbs_c1")
        for module_name in verb_modules:
            with self.subTest(module=module_name):
                content = importlib.import_module(f"app.modules.{module_name}.content")
                service = importlib.import_module(f"app.modules.{module_name}.service")
                card = content.load_cards()[0]
                order = service.option_order(77, card)
                self.assertEqual(order, service.option_order(77, card))
                self.assertEqual(list(range(len(card.quiz.options))), sorted(order))


class AnswerLeakContractTests(unittest.TestCase):
    def test_quiz_headers_do_not_reveal_studied_unit(self) -> None:
        grammar_modules = ("grammar_a1_a2", "grammar_b1_b2", "grammar_c1")
        for module_name in grammar_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for topic in content.load_topics():
                header = handlers._render_quiz(topic, 0, 101).splitlines()[0]
                self.assertNotIn(topic.title_en.casefold(), header.casefold(), topic.id)

        verb_modules = ("verbs_a1_a2", "verbs_b1_b2", "verbs_c1")
        for module_name in verb_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for card in content.load_cards():
                header = handlers._render_quiz(card, 101).splitlines()[0]
                self.assertNotIn(card.title_en.casefold(), header.casefold(), card.id)

        card_modules = (
            ("collocations_intermediate", "phrase"),
            ("collocations_advanced", "phrase"),
            ("phrasal_verbs_intermediate", "phrase"),
            ("phrasal_verbs_advanced", "phrase"),
            ("idioms_intermediate", "idiom"),
            ("idioms_advanced", "idiom"),
            ("irregular_verbs", "infinitive"),
        )
        for module_name, target_attribute in card_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for card in content.load_cards():
                target = str(getattr(card, target_attribute))
                header = handlers._render_quiz(card, 101).splitlines()[0]
                self.assertNotIn(target.casefold(), header.casefold(), card.id)

        topic_modules = ("modal_verbs", "verb_patterns")
        for module_name in topic_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for topic in content.load_topics():
                header = handlers._render_quiz(topic, 0, 101).splitlines()[0]
                self.assertNotIn(topic.title_en.casefold(), header.casefold(), topic.id)

    def test_confirmed_prompts_no_longer_contain_the_answer(self) -> None:
        cases = (
            ("collocations_intermediate", "coll_int_045_update_an_app"),
            ("word_formation", "wf_029_conversion_to_verb"),
            ("word_formation", "wf_037_flat_adverbs"),
        )
        for module_name, item_id in cases:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            card = next(item for item in content.load_cards() if item.id == item_id)
            correct = card.quiz.options[card.quiz.correct_index]
            self.assertNotIn(correct.casefold(), card.quiz.prompt.casefold(), item_id)


if __name__ == "__main__":
    unittest.main()

