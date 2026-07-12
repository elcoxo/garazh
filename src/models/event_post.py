from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.enums import AIProvider


class EventPost(BaseModel):
    __tablename__ = 'event_posts'
    __table_args__ = (
        UniqueConstraint('chat_id', 'message_id', name='source'),
    )

    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    chat_title: Mapped[str | None] = mapped_column(String(256))
    chat_username: Mapped[str | None] = mapped_column(String(64))
    author_name: Mapped[str | None] = mapped_column(String(256))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    text: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[str | None] = mapped_column(String(256))

    extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extracted_by: Mapped[AIProvider | None] = mapped_column(Enum(AIProvider, name='ai_provider'))
    extraction_error: Mapped[str | None] = mapped_column(Text)

    events: Mapped[list['Event']] = relationship(back_populates='post')

    @property
    def post_url(self) -> str | None:
        if not self.message_id or not (self.chat_username or self.chat_id):
            return None
        return (
            f'https://t.me/{self.chat_username}/{self.message_id}'
            if self.chat_username
            else f'https://t.me/c/{abs(self.chat_id)}/{self.message_id}'
        )
