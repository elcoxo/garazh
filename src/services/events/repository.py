from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Event, EventPost, UserCalendar, UserEvent
from models.enums import AIProvider
from services.ai.schemas import EventDraft
from services.events.schemas import ForwardInput


async def get_event_post(
        session: AsyncSession,
        chat_id: int,
        message_id: int,
) -> EventPost | None:
    stmt = (
        select(EventPost)
        .options(selectinload(EventPost.events).selectinload(Event.post))
        .where(
            EventPost.chat_id == chat_id,
            EventPost.message_id == message_id,
        )
    )
    return await session.scalar(stmt)


async def get_or_create_event_post(session: AsyncSession, data: ForwardInput) -> EventPost:
    if data.chat_id is not None and data.message_id is not None:
        post = await get_event_post(session, data.chat_id, data.message_id)
        if post is not None:
            return post
    return await create_event_post(session, data)


async def create_event_post(session: AsyncSession, data: ForwardInput) -> EventPost:
    post = EventPost(
        chat_id=data.chat_id,
        message_id=data.message_id,
        chat_title=data.chat_title,
        chat_username=data.chat_username,
        author_name=data.author_name,
        posted_at=data.posted_at,
        text=data.text,
        media_file_id=data.media_file_id,
        events=[],
    )
    session.add(post)
    await session.flush()
    return post


async def save_event_from_draft(
        session: AsyncSession,
        post: EventPost,
        draft: EventDraft,
        extracted_by: AIProvider,
) -> Event:
    event = Event(
        post=post,
        summary=draft.summary,
        description=draft.description,
        location=draft.location,
        url=draft.url,
        dtstart=draft.dtstart,
        dtend=draft.dtend,
        all_day=draft.all_day,
    )
    session.add(event)
    post.extracted_at = datetime.now(timezone.utc)
    post.extracted_by = extracted_by
    post.extraction_error = None
    await session.flush()
    return event


async def get_user_event_for_post(
        session: AsyncSession, user_id: int, post_id: int,
) -> Event | None:
    stmt = (
        select(Event)
        .join(UserEvent, UserEvent.event_id == Event.id)
        .where(UserEvent.user_id == user_id, Event.post_id == post_id)
        .limit(1)
    )
    return await session.scalar(stmt)


async def get_event(session: AsyncSession, event_id: int) -> Event | None:
    return await session.get(Event, event_id, options=[selectinload(Event.post)])


async def get_user_event(
        session: AsyncSession, user_id: int, event_id: int,
) -> UserEvent | None:
    stmt = (
        select(UserEvent)
        .options(
            selectinload(UserEvent.calendar).selectinload(UserCalendar.oauth_credential),
        )
        .where(UserEvent.user_id == user_id, UserEvent.event_id == event_id)
    )
    return await session.scalar(stmt)


async def get_upcoming_user_events(
        session: AsyncSession, user_id: int, calendar_id: int, since: datetime,
) -> list[UserEvent]:
    stmt = (
        select(UserEvent)
        .join(UserEvent.event)
        .options(selectinload(UserEvent.event))
        .where(
            UserEvent.user_id == user_id,
            UserEvent.calendar_id == calendar_id,
            UserEvent.external_event_id.is_not(None),
            Event.dtstart >= since,
        )
    )
    result = await session.scalars(stmt)
    return list(result.all())


async def list_upcoming_events(session: AsyncSession, user_id: int, since: datetime) -> list[Event]:
    stmt = (
        select(Event)
        .join(UserEvent, UserEvent.event_id == Event.id)
        .options(selectinload(Event.post))
        .where(UserEvent.user_id == user_id, Event.dtstart >= since)
        .order_by(Event.dtstart.asc())
        .limit(20)
    )
    result = await session.scalars(stmt)
    return list(result.all())
