from __future__ import annotations

import importlib
import inspect
import unittest
from pathlib import Path

from aiogram.filters.callback_data import CallbackData

from app.callbacks import SectionCallback
from app.handlers import navigation
from app.keyboards.main import get_main_menu_keyboard
from app.learning import CONTINUE_TARGETS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _callback_values(markup: object) -> set[str]:
    return {
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    }


class MenuContractTests(unittest.TestCase):
    def test_main_menu_has_all_top_level_entries(self) -> None:
        callbacks = _callback_values(get_main_menu_keyboard())
        expected_sections = {
            "grammar",
            "verbs",
            "collocations",
            "phrasal_verbs",
            "idioms",
            "word_formation",
            "continue_learning",
        }
        for name in expected_sections:
            self.assertIn(SectionCallback(name=name).pack(), callbacks)
        self.assertTrue(any(value.startswith("lpa:") for value in callbacks))

    def test_verbs_menu_exposes_specialized_courses(self) -> None:
        callbacks = _callback_values(navigation.get_verbs_choice_keyboard())
        for name in ("verbs_a1_a2", "verbs_b1_b2", "verbs_c1", "modal_verbs",
                     "irregular_verbs", "verb_patterns"):
            self.assertIn(SectionCallback(name=name).pack(), callbacks)

    def test_collocations_menu_exposes_both_levels(self) -> None:
        callbacks = _callback_values(navigation.get_collocations_choice_keyboard())
        self.assertIn(SectionCallback(name="collocations_intermediate").pack(), callbacks)
        self.assertIn(SectionCallback(name="collocations_advanced").pack(), callbacks)

    def test_continue_targets_cover_every_course(self) -> None:
        self.assertEqual(16, len(CONTINUE_TARGETS))
        self.assertEqual(16, len({item.progress_table for item in CONTINUE_TARGETS}))
        self.assertTrue(all(len(item.callback_data.encode("utf-8")) <= 64 for item in CONTINUE_TARGETS))

    def test_every_course_home_can_open_first_material(self) -> None:
        grammar_modules = ("grammar_a1_a2", "grammar_b1_b2", "grammar_c1")
        for module_name in grammar_modules:
            keyboards = importlib.import_module(f"app.modules.{module_name}.keyboards")
            callbacks = _callback_values(
                keyboards.build_course_home(
                    has_active_attempt=False,
                    has_progress=False,
                )
            )
            self.assertTrue(any(":open:1" in value for value in callbacks), module_name)

        card_modules = (
            "verbs_a1_a2",
            "verbs_b1_b2",
            "verbs_c1",
            "irregular_verbs",
            "verb_patterns",
            "modal_verbs",
            "collocations_intermediate",
            "collocations_advanced",
            "phrasal_verbs_intermediate",
            "phrasal_verbs_advanced",
            "idioms_intermediate",
            "idioms_advanced",
            "word_formation",
        )
        for module_name in card_modules:
            keyboards = importlib.import_module(f"app.modules.{module_name}.keyboards")
            callbacks = _callback_values(keyboards.build_course_home(has_progress=False))
            self.assertTrue(any(":open:1" in value for value in callbacks), module_name)

        advanced_result_callbacks = _callback_values(
            importlib.import_module(
                "app.modules.collocations_advanced.keyboards"
            ).build_result(1)
        )
        self.assertTrue(any(value.startswith("cxpa:") for value in advanced_result_callbacks))


class CallbackContractTests(unittest.TestCase):
    def test_callback_prefixes_are_unique(self) -> None:
        prefixes: dict[str, str] = {}
        duplicates: list[str] = []
        for path in sorted((PROJECT_ROOT / "app").rglob("callbacks.py")):
            relative = path.relative_to(PROJECT_ROOT).with_suffix("")
            module = importlib.import_module(".".join(relative.parts))
            for name, value in inspect.getmembers(module, inspect.isclass):
                if value is CallbackData or not issubclass(value, CallbackData):
                    continue
                prefix = value.__prefix__
                owner = f"{module.__name__}.{name}"
                if prefix in prefixes and prefixes[prefix] != owner:
                    duplicates.append(f"{prefix}: {prefixes[prefix]} / {owner}")
                prefixes[prefix] = owner
        self.assertGreaterEqual(len(prefixes), 56)
        self.assertEqual([], duplicates)

    def test_representative_callbacks_fit_telegram_limit(self) -> None:
        samples: list[str] = []
        for path in sorted((PROJECT_ROOT / "app").rglob("callbacks.py")):
            source = path.read_text(encoding="utf-8")
            for prefix in ("prefix=\"", "prefix='"):
                start = 0
                while True:
                    start = source.find(prefix, start)
                    if start < 0:
                        break
                    start += len(prefix)
                    end = source.find(prefix[-1], start)
                    samples.append(source[start:end])
                    start = end + 1
        self.assertTrue(samples)
        self.assertTrue(all(len(value.encode("utf-8")) <= 64 for value in samples))


class DispatcherContractTests(unittest.TestCase):
    def test_dispatcher_factory_registers_every_router(self) -> None:
        main = importlib.import_module("app.main")
        dispatcher = main.create_dispatcher()
        names = {router.name for router in dispatcher.sub_routers}
        expected = {
            "app.modules.level_test.handlers",
            "app.modules.grammar_a1_a2.handlers",
            "app.modules.grammar_b1_b2.handlers",
            "app.modules.grammar_c1.handlers",
            "app.modules.verbs_a1_a2.handlers",
            "app.modules.verbs_b1_b2.handlers",
            "app.modules.verbs_c1.handlers",
            "app.modules.irregular_verbs.handlers",
            "app.modules.verb_patterns.handlers",
            "app.modules.modal_verbs.handlers",
            "app.modules.collocations_intermediate.handlers",
            "app.modules.collocations_advanced.handlers",
            "app.modules.phrasal_verbs_intermediate.handlers",
            "app.modules.phrasal_verbs_advanced.handlers",
            "app.modules.idioms_intermediate.handlers",
            "app.modules.idioms_advanced.handlers",
            "app.modules.word_formation.handlers",
            "main_menu",
            "navigation",
        }
        self.assertTrue(expected.issubset(names), expected - names)

    def test_every_answer_repository_has_idempotency_guard(self) -> None:
        missing: list[str] = []
        for path in sorted((PROJECT_ROOT / "app" / "modules").glob("*/repository.py")):
            source = path.read_text(encoding="utf-8")
            if "async def record_answer" not in source or "level_test" in path.parts:
                continue
            if "@idempotent_answer(AnswerResult)" not in source:
                missing.append(str(path.relative_to(PROJECT_ROOT)))
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
