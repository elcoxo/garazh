import uuid
from datetime import datetime, timezone
from typing import Annotated

import redis.asyncio as aioredis
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from bot import bot
from bot.keyboards import get_user_context, main_keyboard
from db.redis import pool
from services.calendar.constants import GOOGLE_AUTH_URL, GOOGLE_SCOPE, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL
from db.session import get_session
from models.enums import ProviderSlug
from models.oauth_credential import OAuthCredential
from models.user import User
from settings import get_settings

cfg = get_settings()

router = APIRouter(prefix='/auth', tags=['auth'])


SessionDep = Annotated[AsyncSession, Depends(get_session)]

_CONNECT_TOKEN_TTL = 600
_OAUTH_STATE_TTL = 600


def _google_client() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=cfg.google_client_id,
        client_secret=cfg.google_client_secret,
        redirect_uri=f'{cfg.app_base_url}/auth/google/callback',
        scope=GOOGLE_SCOPE,
    )


@router.get('/google')
async def google_auth(token: str) -> RedirectResponse:
    redis = aioredis.Redis(connection_pool=pool)
    user_id_bytes = await redis.getdel(f'connect_token:{token}')
    if not user_id_bytes:
        raise HTTPException(status_code=400, detail='Invalid or expired link')

    state = str(uuid.uuid4())
    await redis.setex(f'oauth_state:{state}', _OAUTH_STATE_TTL, user_id_bytes)

    client = _google_client()
    url, _ = client.create_authorization_url(
        GOOGLE_AUTH_URL,
        state=state,
        access_type='offline',
        prompt='consent',
    )
    return RedirectResponse(url)


@router.get('/google/callback')
async def google_callback(code: str, state: str, session: SessionDep) -> dict:
    redis = aioredis.Redis(connection_pool=pool)
    user_id_bytes = await redis.getdel(f'oauth_state:{state}')
    if not user_id_bytes:
        raise HTTPException(status_code=400, detail='Invalid or expired state')

    user_id = int(user_id_bytes)

    async with _google_client() as client:
        token = await client.fetch_token(GOOGLE_TOKEN_URL, code=code)
        userinfo = (await client.get(GOOGLE_USERINFO_URL)).json()

    result = await session.execute(
        select(OAuthCredential).where(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == ProviderSlug.GOOGLE,
        )
    )
    credential = result.scalar_one_or_none()

    if credential is None:
        credential = OAuthCredential(user_id=user_id, provider=ProviderSlug.GOOGLE)
        session.add(credential)

    credential.access_token = token['access_token']
    credential.refresh_token = token.get('refresh_token')
    credential.token_expiry = (
        datetime.fromtimestamp(token['expires_at'], tz=timezone.utc)
        if 'expires_at' in token
        else None
    )
    credential.email = userinfo.get('email')
    await session.commit()

    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            joinedload(User.settings),
            selectinload(User.oauth_credentials),
            selectinload(User.calendars),
        )
    )
    user = result.scalar_one_or_none()
    if user:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputRichMessage

        ctx = await get_user_context(user)
        await bot.send_rich_message(
            chat_id=user.tg_id,
            rich_message=InputRichMessage(markdown='✓ Вход успешно выполнен!'),
            reply_markup=main_keyboard(ctx),
        )
        await bot.send_rich_message(
            chat_id=user.tg_id,
            rich_message=InputRichMessage(
                markdown='# Календарь\n\nВыберите календарь для синхронизации событий.\n',
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Выбрать календарь', callback_data='calendar:change')],
            ]),
        )

    return {'status': 'ok', 'message': 'Google Calendar connected!'}
