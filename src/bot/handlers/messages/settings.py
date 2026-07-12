import json
import uuid

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputRichMessage, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import get_user_context, main_keyboard, settings_inline_keyboard
from db.redis import pool
from db.redis import redis_client
from models import User
from models.user_calendar import UserCalendar
from models.user_settings import UserSettings
from services.calendar import list_calendars
from settings import get_settings

cfg = get_settings()


async def _fetch_and_cache_calendars(db_user: User, session: AsyncSession) -> dict[str, dict[str, str]] | None:
    credential = db_user.oauth_credential
    if credential is None:
        return None
    calendars = await list_calendars(session, credential)
    cal_map = {str(i): {'id': cal.id, 'name': cal.name, 'timezone': cal.timezone} for i, cal in enumerate(calendars)}
    await redis_client.setex(f'cal_list:{db_user.id}', 300, json.dumps(cal_map))
    return cal_map


@telegram_router.message(F.text == 'Настройки')
async def btn_settings(message: Message, db_user: User, session: AsyncSession) -> None:
    ctx = await get_user_context(db_user)
    await message.answer_rich(
        rich_message=InputRichMessage(markdown='# Настройки'),
        reply_markup=settings_inline_keyboard(ctx),
    )


@telegram_router.callback_query(F.data == 'settings:toggle_auto_add')
async def cb_toggle_auto_add(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    settings = db_user.settings
    if settings is None:
        settings = UserSettings(user_id=db_user.id, auto_add=True)
        session.add(settings)
        db_user.settings = settings
    else:
        settings.auto_add = not settings.auto_add
    await session.commit()

    ctx = await get_user_context(db_user)
    await callback.message.edit_reply_markup(reply_markup=settings_inline_keyboard(ctx))
    await callback.answer('Авто-добавление включено' if settings.auto_add else 'Авто-добавление выключено')


@telegram_router.callback_query(F.data == 'settings:calendar')
async def cb_settings_calendar(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    cal_map = await _fetch_and_cache_calendars(db_user, session)
    if cal_map is None:
        await callback.answer('Сначала подключи календарь', show_alert=True)
        return

    selected = db_user.calendar
    credential = db_user.oauth_credential

    lines = ['# Календарь']
    if credential and credential.email:
        lines.append(f'Почта: `{credential.email}`\n')
    for entry in cal_map.values():
        is_selected = selected and selected.calendar_id == entry['id']
        checkbox = '- [x]' if is_selected else '- [ ]'
        lines.append(f'{checkbox} {entry["name"]}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить', callback_data='calendar:change')],
        [InlineKeyboardButton(text='Отключить', callback_data='settings:disconnect')],
        [InlineKeyboardButton(text='Настройки', callback_data='calendar:back')],
    ])

    await callback.message.edit_text(
        rich_message=InputRichMessage(markdown='\n'.join(lines)),
        reply_markup=keyboard,
    )
    await callback.answer()


@telegram_router.callback_query(F.data == 'calendar:change')
async def cb_calendar_change(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    cal_map_raw = await redis_client.get(f'cal_list:{db_user.id}')

    if cal_map_raw:
        cal_map = json.loads(cal_map_raw)
    else:
        cal_map = await _fetch_and_cache_calendars(db_user, session)
        if cal_map is None:
            await callback.answer('Сначала подключи календарь', show_alert=True)
            return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *[[InlineKeyboardButton(text=v['name'], callback_data=f'calendar:select:{i}')] for i, v in cal_map.items()],
        [InlineKeyboardButton(text='Назад', callback_data='settings:calendar')],
    ])
    await callback.message.edit_text(
        rich_message=InputRichMessage(markdown='# Календарь\n\nВыбери из списка:'),
        reply_markup=keyboard,
    )
    await callback.answer()


@telegram_router.callback_query(F.data.startswith('calendar:select:'))
async def cb_calendar_select(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    idx = callback.data.split(':')[-1]

    cal_map_raw = await redis_client.get(f'cal_list:{db_user.id}')
    if not cal_map_raw:
        await callback.answer('Сессия истекла, открой настройки снова', show_alert=True)
        return

    cal_map = json.loads(cal_map_raw)
    cal_entry = cal_map.get(idx)
    if not cal_entry:
        await callback.answer('Ошибка выбора', show_alert=True)
        return
    external_id = cal_entry['id']
    external_name = cal_entry['name']
    external_timezone = cal_entry.get('timezone', 'Europe/Moscow')

    user_calendar = db_user.calendar

    if user_calendar is None:
        credential = db_user.oauth_credential
        if not credential:
            await callback.answer('Сначала подключи календарь', show_alert=True)
            return
        user_calendar = UserCalendar(
            user_id=db_user.id,
            oauth_credential_id=credential.id,
            calendar_id=external_id,
            calendar_name=external_name,
            calendar_timezone=external_timezone,
        )
        session.add(user_calendar)
        db_user.calendars.append(user_calendar)
    else:
        user_calendar.calendar_id = external_id
        user_calendar.calendar_name = external_name
        user_calendar.calendar_timezone = external_timezone

    await session.commit()
    await callback.answer('✓ Календарь выбран')

    ctx = await get_user_context(db_user)
    await callback.message.edit_text(
        rich_message=InputRichMessage(markdown='# Настройки'),
        reply_markup=settings_inline_keyboard(ctx),
    )


@telegram_router.callback_query(F.data == 'calendar:back')
async def cb_calendar_back(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    ctx = await get_user_context(db_user)
    await callback.message.edit_text(
        rich_message=InputRichMessage(markdown='# Настройки'),
        reply_markup=settings_inline_keyboard(ctx),
    )
    await callback.answer()


@telegram_router.callback_query(F.data == 'settings:reconnect')
async def cb_settings_reconnect(callback: CallbackQuery, db_user: User) -> None:
    token = str(uuid.uuid4())
    await redis_client.setex(f'connect_token:{token}', 600, str(db_user.id))
    url = f'{cfg.app_base_url}/auth/google?token={token}'
    await callback.message.edit_text(f'Подключи Google Calendar:\n{url}')
    await callback.answer()


@telegram_router.callback_query(F.data == 'settings:disconnect')
async def cb_settings_disconnect(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    user_calendar = db_user.calendar
    if user_calendar:
        await session.delete(user_calendar)
        db_user.calendars.remove(user_calendar)

    credential = db_user.oauth_credential
    if credential:
        await session.delete(credential)
        db_user.oauth_credentials.remove(credential)

    await session.commit()

    ctx = await get_user_context(db_user)
    await callback.message.delete()
    await callback.message.answer('Календарь отключен', reply_markup=main_keyboard(ctx))
    await callback.answer()


@telegram_router.callback_query(F.data == 'settings:close')
async def cb_settings_close(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()
