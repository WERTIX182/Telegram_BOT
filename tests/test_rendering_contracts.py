from __future__ import annotations

import importlib
import unittest


class RenderingContractTests(unittest.TestCase):
    def test_every_theory_and_quiz_screen_fits_telegram_text_limit(self) -> None:
        grammar_modules = ("grammar_a1_a2", "grammar_b1_b2", "grammar_c1")
        for module_name in grammar_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for topic in content.load_topics():
                self.assertLessEqual(len(handlers._render_topic(topic)), 4096, topic.id)
                for index in range(len(topic.quizzes)):
                    self.assertLessEqual(
                        len(handlers._render_quiz(topic, index, 123)),
                        4096,
                        f"{topic.id}#{index}",
                    )

        card_modules = (
            "verbs_a1_a2",
            "verbs_b1_b2",
            "verbs_c1",
            "irregular_verbs",
            "collocations_intermediate",
            "collocations_advanced",
            "phrasal_verbs_intermediate",
            "phrasal_verbs_advanced",
            "idioms_intermediate",
            "idioms_advanced",
            "word_formation",
        )
        for module_name in card_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for card in content.load_cards():
                self.assertLessEqual(len(handlers._render_card(card)), 4096, card.id)
                self.assertLessEqual(len(handlers._render_quiz(card, 123)), 4096, card.id)

        topic_modules = ("modal_verbs", "verb_patterns")
        for module_name in topic_modules:
            content = importlib.import_module(f"app.modules.{module_name}.content")
            handlers = importlib.import_module(f"app.modules.{module_name}.handlers")
            for topic in content.load_topics():
                self.assertLessEqual(len(handlers._render_topic(topic)), 4096, topic.id)
                for index in range(len(topic.quizzes)):
                    self.assertLessEqual(
                        len(handlers._render_quiz(topic, index, 123)),
                        4096,
                        f"{topic.id}#{index}",
                    )


if __name__ == "__main__":
    unittest.main()

