from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel


class Event(BaseModel):
    __tablename__ = 'events'

    post_id: Mapped[int | None] = mapped_column(ForeignKey('event_posts.id'))
    parent_event_id: Mapped[int | None] = mapped_column(ForeignKey('events.id'))

    uid: Mapped[UUID] = mapped_column(Uuid, unique=True, default=uuid4)
    summary: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(512))
    dtstart: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dtend: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)

    post: Mapped['EventPost | None'] = relationship(back_populates='events')
    user_events: Mapped[list['UserEvent']] = relationship(back_populates='event')
