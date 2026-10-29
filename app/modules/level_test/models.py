from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class PlacementTestAttempt(Base):
    __tablename__ = "placement_test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    test_version: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="in_progress", index=True)
    current_position: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    question_order_json: Mapped[str] = mapped_column(Text)
    option_orders_json: Mapped[str] = mapped_column(Text)
    result_level: Mapped[str | None] = mapped_column(String(8), nullable=True)
    recommended_start_level: Mapped[str | None] = mapped_column(String(8), nullable=True)
    result_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_is_borderline: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    band_scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["PlacementTestAnswer"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )

class PlacementTestAnswer(Base):
    __tablename__ = "placement_test_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_placement_answer_attempt_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("placement_test_attempts.id", ondelete="CASCADE"),
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(32), index=True)
    question_level: Mapped[str] = mapped_column(String(8), index=True)
    display_option: Mapped[int] = mapped_column(Integer)
    canonical_option: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    attempt: Mapped[PlacementTestAttempt] = relationship(back_populates="answers")
