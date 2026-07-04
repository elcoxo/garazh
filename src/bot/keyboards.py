from dataclasses import dataclass, field

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from models.enums import ProviderSlug
from models.user import User
from models.user_calendar import UserCalendar


@dataclass
class UserContext:
    calendar_connected: bool
    auto_add: bool
    calendar_provider: ProviderSlug | None = field(default=None)
    calendar_email: str | None = field(default=None)
    selected_calendar: UserCalendar | None = field(default=None)


async def get_user_context(user: User) -> UserContext:
    credential = user.oauth_credential
    return UserContext(
        calendar_connected=credential is not None,
        auto_add=user.settings.auto_add if user.settings else False,
        calendar_provider=credential.provider if credential else None,
        calendar_email=credential.email if credential else None,
        selected_calendar=user.calendar,
    )


def main_keyboard(ctx: UserContext) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []

    if ctx.calendar_connected:
        rows.append([KeyboardButton(text='Настройки')])
    else:
        rows.append([KeyboardButton(text='Подключить календарь')])

    rows.append([KeyboardButton(text='Поддержка')])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True, selective=False)


def event_preview_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='＋ Добавить', callback_data=f'event:add:{event_id}'),
        InlineKeyboardButton(text='✕ Отмена', callback_data=f'event:cancel:{event_id}'),
    ]])


def settings_inline_keyboard(ctx: UserContext) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    auto_add_label = '✓ Авто-добавление' if ctx.auto_add else 'Авто-добавление'
    rows.append([InlineKeyboardButton(text=auto_add_label, callback_data='settings:toggle_auto_add')])

    if ctx.calendar_connected:
        if ctx.selected_calendar:
            cal_label = f'Календарь: {ctx.selected_calendar.calendar_name or ctx.selected_calendar.calendar_id}'
        else:
            cal_label = f'Выбрать календарь'
        rows.append([InlineKeyboardButton(text=cal_label, callback_data='settings:calendar')])

    rows.append([InlineKeyboardButton(text='Закрыть', callback_data='settings:close')])

    return InlineKeyboardMarkup(inline_keyboard=rows)
