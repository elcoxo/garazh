from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.enums import EventStatus


class UserEvent(BaseModel):
    __tablename__ = 'user_events'
    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='user_event'),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'), index=True)
    calendar_id: Mapped[int] = mapped_column(ForeignKey('user_calendars.id'))

    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name='event_status'), default=EventStatus.PENDING)
    external_event_id: Mapped[str | None] = mapped_column(String(256))

    user: Mapped['User'] = relationship(back_populates='user_events')
    event: Mapped['Event'] = relationship(back_populates='user_events')
    calendar: Mapped['UserCalendar'] = relationship(back_populates='user_events')
