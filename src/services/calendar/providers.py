from sqlalchemy.ext.asyncio import AsyncSession

from models.caldav_credential import CalDAVCredential
from models.enums import ProviderSlug
from models.oauth_credential import OAuthCredential
from services.calendar.base import CalendarProvider
from services.calendar.google import GoogleCalendarProvider


def get_calendar_provider(
    credential: OAuthCredential | CalDAVCredential,
    session: AsyncSession,
) -> CalendarProvider:
    if isinstance(credential, OAuthCredential) and credential.provider == ProviderSlug.GOOGLE:
        return GoogleCalendarProvider(credential, session)
    raise ValueError(f'Unsupported credential: {credential}')
