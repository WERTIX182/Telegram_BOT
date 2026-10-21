from __future__ import annotations

import unittest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from scripts.migrate_stage2_database import migrate_database


class DatabaseContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_clean_database_has_foreign_keys_enabled(self) -> None:
        import app.main  # noqa: F401 - registers every model
        from app.database.base import Base
        from app.database.engine import create_project_engine

        engine = create_project_engine("sqlite+aiosqlite:///:memory:", echo=False)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
                enabled = await connection.scalar(text("PRAGMA foreign_keys"))
                violations = (await connection.execute(text("PRAGMA foreign_key_check"))).all()
            self.assertEqual(1, enabled)
            self.assertEqual([], violations)
            self.assertEqual(61, len(Base.metadata.tables))
        finally:
            await engine.dispose()

    async def test_parallel_answer_is_idempotent(self) -> None:
        import app.main  # noqa: F401 - registers every model
        from app.database.base import Base
        from app.database.engine import create_project_engine
        from app.database.users import upsert_telegram_user
        from app.modules.verbs_a1_a2.content import get_card
        from app.modules.verbs_a1_a2.models import VerbProgress, VerbQuizAnswer
        from app.modules.verbs_a1_a2.repository import (
            get_attempt_for_user,
            record_answer,
            start_attempt,
        )

        with TemporaryDirectory() as directory:
            database = Path(directory) / "parallel.db"
            engine = create_project_engine(
                f"sqlite+aiosqlite:///{database.as_posix()}",
                echo=False,
            )
            factory = async_sessionmaker(engine, expire_on_commit=False)
            try:
                async with engine.begin() as connection:
                    await connection.run_sync(Base.metadata.create_all)
                async with factory() as session:
                    await upsert_telegram_user(
                        session,
                        telegram_id=777,
                        first_name="Test",
                        last_name=None,
                        username=None,
                    )
                    attempt = await start_attempt(session, 777, get_card(1))
                    attempt_id = attempt.id

                session_one = factory()
                session_two = factory()
                try:
                    attempt_one = await get_attempt_for_user(session_one, attempt_id, 777)
                    attempt_two = await get_attempt_for_user(session_two, attempt_id, 777)
                    results = await asyncio.gather(
                        record_answer(
                            session_one,
                            attempt=attempt_one,
                            card=get_card(1),
                            option_index=get_card(1).quiz.correct_index,
                        ),
                        record_answer(
                            session_two,
                            attempt=attempt_two,
                            card=get_card(1),
                            option_index=get_card(1).quiz.correct_index,
                        ),
                    )
                finally:
                    await session_one.close()
                    await session_two.close()

                self.assertEqual(1, sum(result.accepted for result in results))
                async with factory() as session:
                    answer_count = await session.scalar(select(func.count()).select_from(VerbQuizAnswer))
                    progress = await session.scalar(select(VerbProgress).where(VerbProgress.user_id == 777))
                self.assertEqual(1, answer_count)
                self.assertEqual(1, progress.total_answers)
            finally:
                await engine.dispose()

    async def test_grammar_quiz_resumes_and_completes(self) -> None:
        import app.main  # noqa: F401 - registers every model
        from app.database.base import Base
        from app.database.engine import create_project_engine
        from app.database.users import upsert_telegram_user
        from app.learning import find_continue_target
        from app.modules.grammar_a1_a2.content import get_topic
        from app.modules.grammar_a1_a2.repository import (
            get_active_attempt,
            get_or_create_progress,
            record_answer,
            start_attempt,
        )
        from app.modules.grammar_a1_a2.service import parse_topic_set

        with TemporaryDirectory() as directory:
            database = Path(directory) / "resume.db"
            engine = create_project_engine(
                f"sqlite+aiosqlite:///{database.as_posix()}",
                echo=False,
            )
            factory = async_sessionmaker(engine, expire_on_commit=False)
            try:
                async with engine.begin() as connection:
                    await connection.run_sync(Base.metadata.create_all)
                topic = get_topic(1)
                async with factory() as session:
                    await upsert_telegram_user(
                        session,
                        telegram_id=888,
                        first_name="Resume",
                        last_name=None,
                        username=None,
                    )
                    attempt = await start_attempt(session, 888, topic)
                    first = await record_answer(
                        session,
                        attempt=attempt,
                        topic=topic,
                        quiz_index=0,
                        option_index=topic.quizzes[0].correct_index,
                    )
                    self.assertTrue(first.accepted)
                    attempt_id = attempt.id

                async with factory() as session:
                    resumed = await get_active_attempt(session, 888)
                    self.assertEqual(attempt_id, resumed.id)
                    self.assertEqual(1, resumed.current_quiz_index)
                    for index in (1, 2):
                        result = await record_answer(
                            session,
                            attempt=resumed,
                            topic=topic,
                            quiz_index=index,
                            option_index=topic.quizzes[index].correct_index,
                        )
                    self.assertTrue(result.is_complete)
                    duplicate = await record_answer(
                        session,
                        attempt=resumed,
                        topic=topic,
                        quiz_index=2,
                        option_index=topic.quizzes[2].correct_index,
                    )
                    self.assertFalse(duplicate.accepted)
                    progress = await get_or_create_progress(session, 888)
                    self.assertIn(1, parse_topic_set(progress.completed_topics_json))
                    target = await find_continue_target(session, 888)
                    self.assertIsNotNone(target)
                    self.assertEqual("grammar_progress", target.progress_table)
            finally:
                await engine.dispose()


class DatabaseMigrationTests(unittest.TestCase):
    def test_migration_backs_up_and_backfills_users(self) -> None:
        import sqlite3

        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "bot.db"
            backup_dir = root / "backups"
            connection = sqlite3.connect(database)
            try:
                connection.executescript(
                    """
                    PRAGMA foreign_keys=OFF;
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id BIGINT NOT NULL UNIQUE,
                        first_name VARCHAR(100) NOT NULL
                    );
                    CREATE TABLE sample_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id BIGINT NOT NULL,
                        value INTEGER NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
                    );
                    INSERT INTO sample_progress(user_id, value) VALUES (101, 7), (202, 8);
                    """
                )
                connection.commit()
            finally:
                connection.close()

            result = migrate_database(database, backup_dir)
            self.assertTrue(result.backup_path.is_file())
            self.assertEqual(2, result.users_added)
            self.assertEqual(2, result.violations_before)
            self.assertEqual(0, result.violations_after)

            migrated = sqlite3.connect(database)
            backup = sqlite3.connect(result.backup_path)
            try:
                self.assertEqual(2, migrated.execute("SELECT COUNT(*) FROM users").fetchone()[0])
                self.assertEqual(2, migrated.execute("SELECT COUNT(*) FROM sample_progress").fetchone()[0])
                self.assertEqual(0, backup.execute("SELECT COUNT(*) FROM users").fetchone()[0])
                self.assertEqual(2, backup.execute("SELECT COUNT(*) FROM sample_progress").fetchone()[0])
                self.assertEqual(("ok",), backup.execute("PRAGMA integrity_check").fetchone())
            finally:
                migrated.close()
                backup.close()


if __name__ == "__main__":
    unittest.main()
