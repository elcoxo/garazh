from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import ProviderSlug
from models.oauth_credential import OAuthCredential
from models.user import User
from services.calendar.base import CalendarProvider
from services.calendar.google import GoogleCalendarProvider


async def get_calendar_provider(user: User, session: AsyncSession) -> CalendarProvider:
    result = await session.execute(
        select(OAuthCredential).where(
            OAuthCredential.user_id == user.id,
            OAuthCredential.provider == ProviderSlug.GOOGLE,
        )
    )
    oauth_credential = result.scalar_one_or_none()
    if oauth_credential:
        return GoogleCalendarProvider(oauth_credential, session)

    raise ValueError('No calendar connected')
