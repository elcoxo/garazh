from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from models import Event, User, UserEvent
from models.enums import EventStatus
from services.ai import extract_event
from services.ai.exceptions import AIDisabledError
from services.ai.schemas import EventDraft
from services.calendar import create_event, delete_event, update_event
from services.events.repository import (
    get_or_create_event_post,
    get_user_event,
    get_user_event_for_post,
    save_event_from_draft,
)
from services.events.schemas import ForwardInput, ForwardOutcome, ForwardResult, SyncOutcome

FALLBACK_DURATION = timedelta(hours=2)
ALL_DAY_THRESHOLD = timedelta(hours=22)


async def process_forward_post(
        session: AsyncSession,
        data: ForwardInput,
        user_id: int,
) -> ForwardResult:
    post = await get_or_create_event_post(session, data)
    if post.events:
        if user_event := await get_user_event_for_post(session, user_id, post.id):
            return ForwardResult(ForwardOutcome.DUPLICATE, event=user_event)
        return ForwardResult(ForwardOutcome.EXTRACTED, event=post.events[0])

    try:
        extraction = await extract_event(data.text, session)
    except AIDisabledError:
        return ForwardResult(ForwardOutcome.AI_DISABLED)

    if extraction.draft is None:
        await session.commit()
        return ForwardResult(ForwardOutcome.NO_EVENT)

    ensure_dtend(extraction.draft)
    event = await save_event_from_draft(session, post, extraction.draft, extracted_by=extraction.provider)
    await session.commit()
    return ForwardResult(ForwardOutcome.EXTRACTED, event=event)


async def remove_event_from_calendar(
        session: AsyncSession,
        user_id: int,
        event: Event,
) -> bool:
    user_event = await get_user_event(session, user_id, event.id)
    if user_event is None:
        return False

    if user_event.external_event_id:
        await delete_event(
            session,
            user_event.calendar.credential,
            user_event.calendar.calendar_id,
            user_event.external_event_id,
        )

    await session.delete(user_event)
    await session.commit()
    return True


async def sync_event_to_calendar(
        session: AsyncSession,
        user: User,
        event: Event,
) -> SyncOutcome:
    user_calendar = user.calendar
    if user_calendar is None:
        return SyncOutcome.NO_CALENDAR

    draft = EventDraft.model_validate(event, from_attributes=True)
    user_event = await get_user_event(session, user.id, event.id)

    if user_event is None:
        external_id = await create_event(
            session, user_calendar.credential, user_calendar.calendar_id, draft,
            timezone=user_calendar.calendar_timezone,
        )
        session.add(UserEvent(
            user_id=user.id,
            event_id=event.id,
            calendar_id=user_calendar.id,
            status=EventStatus.CREATED,
            external_event_id=external_id,
        ))
        await session.commit()
        return SyncOutcome.CREATED

    await update_event(
        session,
        user_event.calendar.credential,
        user_event.calendar.calendar_id,
        user_event.external_event_id,
        draft,
        timezone=user_event.calendar.calendar_timezone,
    )
    return SyncOutcome.UPDATED


def ensure_dtend(draft: EventDraft) -> None:
    if draft.dtend is not None and (draft.dtend - draft.dtstart) >= ALL_DAY_THRESHOLD:
        draft.all_day = True
        draft.dtend = None
        return
    if draft.dtend is None and not draft.all_day:
        draft.dtend = draft.dtstart + FALLBACK_DURATION
