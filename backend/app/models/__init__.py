"""SQLAlchemy models (brief §4)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Supabase user UUID — every analysis belongs to exactly one user; queries
    # are always scoped by this so users never see each other's analyses.
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # uploaded | configured | complete | error
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    files: Mapped[list[FileRecord]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    circuit_name: Mapped[str] = mapped_column(String(255))
    load_type: Mapped[str] = mapped_column(String(40))
    storage_path: Mapped[str] = mapped_column(Text)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    start_ts: Mapped[str | None] = mapped_column(String(40), nullable=True)
    end_ts: Mapped[str | None] = mapped_column(String(40), nullable=True)
    detected_cols_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    flags_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="files")
