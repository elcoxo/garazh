import uuid

import redis.asyncio as aioredis
from loguru import logger
from aiogram import types
from aiogram import F
from aiogram.filters import CommandStart, Command
from aiogram.utils.markdown import hbold
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from bot import telegram_router
from bot.keyboards import get_user_context, main_keyboard, settings_inline_keyboard
from db.redis import pool
from models import User
from models.enums import ProviderSlug
from models.oauth_credential import OAuthCredential
from services.calendar import get_calendar_provider
from settings import get_settings

cfg = get_settings()


@telegram_router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Your ID: {message.from_user.id}")


# @telegram_router.message(CommandStart())
# async def cmd_start(message: Message, db_user: User) -> None:
#     await message.answer(f"Hello, {hbold(db_user.tg_full_name)}!")
@telegram_router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, session: AsyncSession) -> None:
    ctx = await get_user_context(db_user, session)
    await message.answer(f"Hello, {hbold(db_user.tg_full_name)}!", reply_markup=main_keyboard(ctx))


# @telegram_router.message(Command('connect'))
# async def cmd_connect(message: Message, db_user: User) -> None:
#     token = str(uuid.uuid4())
#     redis = aioredis.Redis(connection_pool=pool)
#     await redis.setex(f'connect_token:{token}', 600, str(db_user.id))
#     url = f'{cfg.app_base_url}/auth/google?token={token}'
#     await message.answer(f'Подключи Google Calendar:\n{url}')
@telegram_router.message(F.text == 'Подключить календарь')
@telegram_router.message(Command('connect'))
async def cmd_connect(message: Message, db_user: User) -> None:
    token = str(uuid.uuid4())
    redis = aioredis.Redis(connection_pool=pool)
    await redis.setex(f'connect_token:{token}', 600, str(db_user.id))
    url = f'{cfg.app_base_url}/auth/google?token={token}'
    await message.answer(
        'Подключи свой календарь:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Google Calendar', url=url)],
        ]),
    )


@telegram_router.message(F.text == 'Настройка')
async def btn_settings(message: Message, db_user: User, session: AsyncSession) -> None:
    ctx = await get_user_context(db_user, session)
    await message.answer('⚙️ Настройки:', reply_markup=settings_inline_keyboard(ctx))


@telegram_router.callback_query(F.data == 'settings:reconnect')
async def cb_settings_reconnect(callback: CallbackQuery, db_user: User) -> None:
    token = str(uuid.uuid4())
    redis = aioredis.Redis(connection_pool=pool)
    await redis.setex(f'connect_token:{token}', 600, str(db_user.id))
    url = f'{cfg.app_base_url}/auth/google?token={token}'
    await callback.message.edit_text(f'Подключи Google Calendar:\n{url}')
    await callback.answer()


@telegram_router.callback_query(F.data == 'settings:disconnect')
async def cb_settings_disconnect(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    result = await session.execute(
        select(OAuthCredential).where(
            OAuthCredential.user_id == db_user.id,
            OAuthCredential.provider == ProviderSlug.GOOGLE,
        )
    )
    credential = result.scalar_one_or_none()
    if credential:
        await session.delete(credential)
        await session.commit()

    ctx = await get_user_context(db_user, session)
    await callback.message.delete()
    await callback.message.answer('❌ Google Calendar отключен', reply_markup=main_keyboard(ctx))
    await callback.answer()


@telegram_router.callback_query(F.data == 'settings:close')
async def cb_settings_close(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()


@telegram_router.message(F.text == 'Поддержка')
async def btn_support(message: Message) -> None:
    await message.answer('По всем вопросам: @support')


@telegram_router.message(Command('calendars'))
async def cmd_calendars(message: Message, db_user: User, session: AsyncSession) -> None:
    try:
        provider = await get_calendar_provider(db_user, session)
    except ValueError:
        await message.answer('Сначала подключи календарь: /connect')
        return

    calendars = await provider.list_calendars()
    if not calendars:
        await message.answer('Календари не найдены')
        return

    lines = '\n'.join(f'• {cal.name}' for cal in calendars)
    await message.answer(f'📅 Твои календари:\n\n{lines}')


@telegram_router.message(F.text == "echo")
async def echo(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except Exception as e:
        logger.error(f"Can't send message - {e}")
        await message.answer("Nice try!")


@telegram_router.message(F.text == 'ping')
async def hello(message: types.Message) -> None:
    try:
        await message.answer('pong')
    except Exception as e:
        logger.error(f"Can't send message - {e}")
        await message.answer("Nice try!")
