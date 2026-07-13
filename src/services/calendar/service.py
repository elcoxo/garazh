from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.caldav_credential import CalDAVCredential
from models.enums import ProviderSlug
from models.oauth_credential import OAuthCredential
from services.ai.schemas import EventDraft
from services.calendar.base import CalendarProvider
from services.calendar.exceptions import UnsupportedCredentialError
from services.calendar.google import GoogleCalendarProvider
from services.calendar.schemas import CalendarInfo

Credential = OAuthCredential | CalDAVCredential


async def list_calendars(session: AsyncSession, credential: Credential) -> list[CalendarInfo]:
    return await _get_provider(credential, session).list_calendars()


async def list_event_ids(
    session: AsyncSession,
    credential: Credential,
    calendar_id: str,
    since: datetime,
) -> set[str]:
    return await _get_provider(credential, session).list_event_ids(calendar_id, since)


async def create_event(
    session: AsyncSession,
    credential: Credential,
    calendar_id: str,
    event: EventDraft,
    timezone: str,
) -> str:
    return await _get_provider(credential, session).create_event(calendar_id, event, timezone)


async def update_event(
    session: AsyncSession,
    credential: Credential,
    calendar_id: str,
    external_event_id: str,
    event: EventDraft,
    timezone: str,
) -> None:
    await _get_provider(credential, session).update_event(calendar_id, external_event_id, event, timezone)


async def delete_event(
    session: AsyncSession,
    credential: Credential,
    calendar_id: str,
    external_event_id: str,
) -> None:
    await _get_provider(credential, session).delete_event(calendar_id, external_event_id)


def _get_provider(credential: Credential, session: AsyncSession) -> CalendarProvider:
    if isinstance(credential, OAuthCredential) and credential.provider == ProviderSlug.GOOGLE:
        return GoogleCalendarProvider(credential, session)
    raise UnsupportedCredentialError(f'Unsupported credential: {type(credential).__name__}')
