from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.calendar import get_calendar_provider


@dataclass
class UserContext:
    calendar_connected: bool


async def get_user_context(user: User, session: AsyncSession) -> UserContext:
    try:
        await get_calendar_provider(user, session)
        calendar_connected = True
    except ValueError:
        calendar_connected = False

    return UserContext(calendar_connected=calendar_connected)


def main_keyboard(ctx: UserContext) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []

    if ctx.calendar_connected:
        rows.append([KeyboardButton(text='Настройка')])
    else:
        rows.append([KeyboardButton(text='Подключить календарь')])

    rows.append([KeyboardButton(text='Поддержка')])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def settings_inline_keyboard(ctx: UserContext) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if ctx.calendar_connected:
        rows.append([InlineKeyboardButton(text='Переподключить Google Calendar', callback_data='settings:reconnect')])
        rows.append([InlineKeyboardButton(text='Отключить Google Calendar', callback_data='settings:disconnect')])

    rows.append([InlineKeyboardButton(text='Закрыть', callback_data='settings:close')])

    return InlineKeyboardMarkup(inline_keyboard=rows)
