from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from models import Event

if TYPE_CHECKING:
    from aiogram.types import Message, MessageOriginChannel, MessageOriginChat

    ForwardOrigin = MessageOriginChannel | MessageOriginChat


class ForwardInput(BaseModel):
    chat_id: int | None = None
    message_id: int | None = None
    text: str
    posted_at: datetime | None = None
    chat_title: str | None = None
    chat_username: str | None = None
    author_name: str | None = None
    media_file_id: str | None = None

    @classmethod
    def from_message(cls, origin: ForwardOrigin, text: str, message: Message) -> ForwardInput:
        from aiogram.types import MessageOriginChannel
        photo_id = message.photo[-1].file_id if message.photo else None
        if isinstance(origin, MessageOriginChannel):
            chat, message_id = origin.chat, origin.message_id
        else:
            chat, message_id = origin.sender_chat, None
        return cls(
            chat_id=chat.id,
            message_id=message_id,
            text=text,
            posted_at=origin.date,
            chat_title=chat.title,
            chat_username=chat.username,
            author_name=origin.author_signature,
            media_file_id=photo_id,
        )


class ForwardOutcome(StrEnum):
    EXTRACTED = 'extracted'
    DUPLICATE = 'duplicate'
    NO_EVENT = 'no_event'
    AI_DISABLED = 'ai_disabled'


class SyncOutcome(StrEnum):
    CREATED = 'created'
    UPDATED = 'updated'
    NO_CALENDAR = 'no_calendar'


@dataclass(frozen=True, slots=True)
class ForwardResult:
    outcome: ForwardOutcome
    event: Event | None = None
