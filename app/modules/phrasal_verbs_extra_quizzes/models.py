from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PhrasalVerbExtraPracticeProgress(Base):
    __tablename__ = "phrasal_verb_extra_practice_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_pv_extra_progress_user_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    completed_sets_json: Mapped[str] = mapped_column(Text, default="[]")
    mastered_sets_json: Mapped[str] = mapped_column(Text, default="[]")
    total_answers: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class PhrasalVerbExtraPracticeAttempt(Base):
    __tablename__ = "phrasal_verb_extra_practice_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    level_code: Mapped[str] = mapped_column(String(1), index=True)
    base_card_id: Mapped[str] = mapped_column(String(120), index=True)
    card_order: Mapped[int] = mapped_column(Integer, index=True)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="in_progress", index=True)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answers: Mapped[list["PhrasalVerbExtraPracticeAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class PhrasalVerbExtraPracticeAnswer(Base):
    __tablename__ = "phrasal_verb_extra_practice_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id", "question_index", name="uq_pv_extra_answer_attempt_question"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("phrasal_verb_extra_practice_attempts.id", ondelete="CASCADE"),
        index=True,
    )
    question_index: Mapped[int] = mapped_column(Integer)
    selected_option_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    attempt: Mapped[PhrasalVerbExtraPracticeAttempt] = relationship(back_populates="answers")