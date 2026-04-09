"""Portfolio model (modularized)."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(200), nullable=False, default="My Portfolio")
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    mongo_doc_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    subdomain: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship("User", back_populates="portfolios")

    def __repr__(self) -> str:
        return f"<Portfolio {self.title} ({self.template_id})>"
