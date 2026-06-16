from datetime import datetime, timezone

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from models.oauth_credential import OAuthCredential
from services.ai.base import ParsedEvent
from services.calendar.base import CalendarInfo, CalendarProvider
from services.calendar.constants import GOOGLE_CALENDAR_LIST_URL, GOOGLE_EVENTS_URL, GOOGLE_TOKEN_URL
from settings import get_settings

cfg = get_settings()


def _token_dict(credential: OAuthCredential) -> dict:
    token = {'access_token': credential.access_token, 'token_type': 'Bearer'}
    if credential.refresh_token:
        token['refresh_token'] = credential.refresh_token
    if credential.token_expiry:
        token['expires_at'] = credential.token_expiry.timestamp()
    return token


async def _refresh_if_expired(credential: OAuthCredential, session: AsyncSession) -> OAuthCredential:
    if credential.token_expiry and credential.token_expiry > datetime.now(tz=timezone.utc):
        return credential

    async with AsyncOAuth2Client(
        client_id=cfg.google_client_id,
        client_secret=cfg.google_client_secret,
    ) as client:
        new_token = await client.refresh_token(GOOGLE_TOKEN_URL, refresh_token=credential.refresh_token)

    credential.access_token = new_token['access_token']
    if 'refresh_token' in new_token:
        credential.refresh_token = new_token['refresh_token']
    credential.token_expiry = datetime.fromtimestamp(new_token['expires_at'], tz=timezone.utc)
    await session.commit()
    return credential


class GoogleCalendarProvider(CalendarProvider):
    def __init__(self, credential: OAuthCredential, session: AsyncSession) -> None:
        self._credential = credential
        self._session = session

    async def list_calendars(self) -> list[CalendarInfo]:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            response = await client.get(GOOGLE_CALENDAR_LIST_URL)
            response.raise_for_status()
            items = response.json().get('items', [])
        return [CalendarInfo(id=item['id'], name=item['summary']) for item in items]

    async def create_event(self, calendar_id: str, event: ParsedEvent) -> str:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        body = {
            'summary': event.title,
            'start': {'dateTime': event.start.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': (event.end or event.start).isoformat(), 'timeZone': 'UTC'},
        }
        if event.location:
            body['location'] = event.location
        if event.description:
            body['description'] = event.description

        url = GOOGLE_EVENTS_URL.format(calendar_id=calendar_id)
        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            return response.json()['id']
