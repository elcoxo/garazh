from datetime import datetime, timedelta, timezone

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from models.oauth_credential import OAuthCredential
from services.ai.schemas import EventDraft
from services.calendar.base import CalendarProvider
from services.calendar.constants import GOOGLE_CALENDAR_LIST_URL, GOOGLE_EVENTS_URL, GOOGLE_TOKEN_URL
from services.calendar.exceptions import CalendarError
from services.calendar.schemas import CalendarInfo
from settings import get_settings

cfg = get_settings()

DEFAULT_DURATION = timedelta(hours=2)
DEFAULT_TIMEZONE = 'Europe/Moscow'


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


def _build_event_body(event: EventDraft, timezone: str) -> dict:
    body: dict = {'summary': event.summary}

    if event.all_day:
        start_date = event.dtstart.date()
        end_date = (event.dtend.date() if event.dtend else start_date) + timedelta(days=1)
        body['start'] = {'date': start_date.isoformat()}
        body['end'] = {'date': end_date.isoformat()}
    else:
        end = event.dtend or (event.dtstart + DEFAULT_DURATION)
        body['start'] = {'dateTime': event.dtstart.replace(tzinfo=None).isoformat(), 'timeZone': timezone}
        body['end'] = {'dateTime': end.replace(tzinfo=None).isoformat(), 'timeZone': timezone}

    if event.location:
        body['location'] = event.location
    if event.description:
        body['description'] = event.description
    if event.url and event.url.startswith(('http://', 'https://')):
        body['source'] = {'url': event.url, 'title': 'Garazh'}
    return body


class GoogleCalendarProvider(CalendarProvider):
    def __init__(self, credential: OAuthCredential, session: AsyncSession) -> None:
        self._credential = credential
        self._session = session

    async def list_calendars(self) -> list[CalendarInfo]:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            try:
                response = await client.get(GOOGLE_CALENDAR_LIST_URL)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise CalendarError(f'Google list calendars failed: {e}') from e
            items = response.json().get('items', [])
        return [
            CalendarInfo(id=item['id'], name=item['summary'], timezone=item.get('timeZone', 'Europe/Moscow'))
            for item in items
        ]

    async def create_event(self, calendar_id: str, event: EventDraft, timezone: str) -> str:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        body = _build_event_body(event, timezone)
        url = GOOGLE_EVENTS_URL.format(calendar_id=calendar_id)

        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            try:
                response = await client.post(url, json=body)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise CalendarError(f'Google create event failed: {e}') from e
            return response.json()['id']

    async def update_event(self, calendar_id: str, external_event_id: str, event: EventDraft, timezone: str) -> None:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        body = _build_event_body(event, timezone)
        url = f'{GOOGLE_EVENTS_URL.format(calendar_id=calendar_id)}/{external_event_id}'

        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            try:
                response = await client.patch(url, json=body)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise CalendarError(f'Google update event failed: {e}') from e

    async def delete_event(self, calendar_id: str, external_event_id: str) -> None:
        self._credential = await _refresh_if_expired(self._credential, self._session)
        url = f'{GOOGLE_EVENTS_URL.format(calendar_id=calendar_id)}/{external_event_id}'

        async with AsyncOAuth2Client(token=_token_dict(self._credential)) as client:
            try:
                response = await client.delete(url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise CalendarError(f'Google delete event failed: {e}') from e
