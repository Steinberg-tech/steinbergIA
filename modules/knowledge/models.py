from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from modules.conversations.models import Base
from shared.utils import generate_id, now_utc


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(50), default="faq")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
