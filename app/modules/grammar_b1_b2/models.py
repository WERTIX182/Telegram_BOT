from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GrammarB1B2Progress(Base):
    __tablename__ = "grammar_b1_b2_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_grammar_b1_b2_progress_user_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    course_id: Mapped[str] = mapped_column(String(40), index=True)
    current_topic_order: Mapped[int] = mapped_column(Integer, default=1)
    completed_topics_json: Mapped[str] = mapped_column(Text, default="[]")
    mastered_topics_json: Mapped[str] = mapped_column(Text, default="[]")
    total_answers: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class GrammarB1B2TopicAttempt(Base):
    __tablename__ = "grammar_b1_b2_topic_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    course_id: Mapped[str] = mapped_column(String(40), index=True)
    topic_id: Mapped[str] = mapped_column(String(80), index=True)
    topic_order: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16), default="in_progress", index=True)
    current_quiz_index: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["GrammarB1B2QuizAnswer"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class GrammarB1B2QuizAnswer(Base):
    __tablename__ = "grammar_b1_b2_quiz_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id", "quiz_index", name="uq_grammar_b1_b2_answer_attempt_quiz"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grammar_b1_b2_topic_attempts.id", ondelete="CASCADE"),
        index=True,
    )
    quiz_index: Mapped[int] = mapped_column(Integer)
    selected_option_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    attempt: Mapped[GrammarB1B2TopicAttempt] = relationship(back_populates="answers")