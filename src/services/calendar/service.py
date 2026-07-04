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


async def create_event(
    session: AsyncSession,
    credential: Credential,
    calendar_id: str,
    event: EventDraft,
) -> str:
    return await _get_provider(credential, session).create_event(calendar_id, event)


def _get_provider(credential: Credential, session: AsyncSession) -> CalendarProvider:
    if isinstance(credential, OAuthCredential) and credential.provider == ProviderSlug.GOOGLE:
        return GoogleCalendarProvider(credential, session)
    raise UnsupportedCredentialError(f'Unsupported credential: {type(credential).__name__}')
