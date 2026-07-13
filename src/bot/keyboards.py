from dataclasses import dataclass, field
from datetime import datetime, timedelta

from aiogram_i18n.lazy import LazyProxy as _
from aiogram_i18n.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot import t
from models.enums import ProviderSlug
from models.user import User
from models.user_calendar import UserCalendar

START_TIMES = ((12, 0), (14, 0), (16, 0), (19, 0), (21, 0), (23, 0))
END_OFFSETS_HOURS = (1, 2, 4, 6, 8, 10)

CLOCK_EMOJIS = ('🕛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚')


@dataclass
class UserContext:
    calendar_connected: bool
    use_auto_add: bool
    use_original_url: bool = field(default=False)
    calendar_provider: ProviderSlug | None = field(default=None)
    calendar_email: str | None = field(default=None)
    selected_calendar: UserCalendar | None = field(default=None)


def get_user_context(user: User) -> UserContext:
    credential = user.oauth_credential
    return UserContext(
        calendar_connected=credential is not None,
        use_auto_add=user.settings.use_auto_add if user.settings else False,
        use_original_url=user.settings.use_original_url if user.settings else False,
        calendar_provider=credential.provider if credential else None,
        calendar_email=credential.email if credential else None,
        selected_calendar=user.calendar,
    )


def clock_emoji(hour: int) -> str:
    return CLOCK_EMOJIS[hour % 12]


def main_keyboard(ctx: UserContext) -> ReplyKeyboardMarkup:
    if ctx.calendar_connected:
        rows = [[KeyboardButton(text=t('btn-support-compact')), KeyboardButton(text=t('btn-my-events')), KeyboardButton(text=t('btn-settings-compact'))]]
    else:
        rows = [
            [KeyboardButton(text=t('btn-connect-calendar'))],
            [KeyboardButton(text=t('btn-support'))],
        ]

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True, selective=False)


def event_preview_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_('btn-add'), callback_data=f'event:add:{event_id}')],
        [
            InlineKeyboardButton(text=_('btn-edit'), callback_data=f'event:edit:{event_id}'),
            InlineKeyboardButton(text=_('btn-cancel'), callback_data=f'event:cancel:{event_id}'),
        ],
    ])


def event_edit_field_keyboard(
    event_id: int, field: str, post_url: str | None = None, has_value: bool = False,
) -> InlineKeyboardMarkup:
    rows = []
    if post_url:
        rows.append([InlineKeyboardButton(text=_('btn-post-url'), callback_data=f'event:set_post_url:{event_id}')])
    if has_value:
        rows.append([InlineKeyboardButton(text=_('btn-clear-field'), callback_data=f'event:clear_field:{event_id}:{field}')])  # noqa: E501
    rows.append([InlineKeyboardButton(text=_('btn-back'), callback_data=f'event:edit_field_cancel:{event_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_added_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=_('btn-edit'), callback_data=f'event:edit:{event_id}'),
        InlineKeyboardButton(text=_('btn-remove'), callback_data=f'event:remove:{event_id}'),
    ]])


def event_edit_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_('btn-field-summary'), callback_data=f'event:edit_field:{event_id}:summary')],
        [
            InlineKeyboardButton(text=_('btn-field-location'), callback_data=f'event:edit_field:{event_id}:location'),
            InlineKeyboardButton(text=_('btn-date'), callback_data=f'event:date_open:{event_id}'),
        ],
        [
            InlineKeyboardButton(text=_('btn-field-description'),
                                 callback_data=f'event:edit_field:{event_id}:description'),
            InlineKeyboardButton(text=_('btn-field-url'), callback_data=f'event:edit_field:{event_id}:url'),
        ],
        [
            InlineKeyboardButton(text=_('btn-save'), callback_data=f'event:edit_save:{event_id}'),
            InlineKeyboardButton(text=_('btn-cancel'), callback_data=f'event:edit_back:{event_id}'),
        ],
    ])


def event_date_keyboard(event_id: int, all_day: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    allday_label = _('btn-allday-on') if all_day else _('btn-allday')
    rows.append([InlineKeyboardButton(text=allday_label, callback_data=f'event:date_toggle_allday:{event_id}')])

    date_row = [InlineKeyboardButton(text=_('btn-date-start'), callback_data=f'event:date_show_start:{event_id}')]
    if not all_day:
        date_row.append(InlineKeyboardButton(text=_('btn-date-end'), callback_data=f'event:date_show_end:{event_id}'))
    rows.append(date_row)

    rows.append([
        InlineKeyboardButton(text=_('btn-save'), callback_data=f'event:date_save:{event_id}'),
        InlineKeyboardButton(text=_('btn-back'), callback_data=f'event:date_cancel:{event_id}'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_date_start_keyboard(event_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append(
        [InlineKeyboardButton(text=_('btn-pick-datetime'), callback_data=f'event:date_manual:{event_id}:start')])
    for i in range(0, len(START_TIMES), 2):
        row: list[InlineKeyboardButton] = []
        for h, m in START_TIMES[i:i + 2]:
            row.append(InlineKeyboardButton(
                text=f'{clock_emoji(h)} {h:02d}:{m:02d}',
                callback_data=f'event:date_pick_start:{event_id}:{h:02d}{m:02d}',
            ))
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text=_('btn-save'), callback_data=f'event:date_save:{event_id}'),
        InlineKeyboardButton(text=_('btn-back'), callback_data=f'event:date_picker_back:{event_id}'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_date_end_keyboard(event_id: int, dtstart: datetime) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append([InlineKeyboardButton(text=_('btn-pick-datetime'), callback_data=f'event:date_manual:{event_id}:end')])
    for i in range(0, len(END_OFFSETS_HOURS), 2):
        row: list[InlineKeyboardButton] = []
        for offset in END_OFFSETS_HOURS[i:i + 2]:
            t = dtstart + timedelta(hours=offset)
            row.append(InlineKeyboardButton(
                text=f'{clock_emoji(t.hour)} {t:%H:%M}',
                callback_data=f'event:date_pick_end:{event_id}:{offset}',
            ))
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text=_('btn-save'), callback_data=f'event:date_save:{event_id}'),
        InlineKeyboardButton(text=_('btn-back'), callback_data=f'event:date_picker_back:{event_id}'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_inline_keyboard(ctx: UserContext) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    use_auto_add_label = _('btn-autoadd-on') if ctx.use_auto_add else _('btn-autoadd')
    rows.append([InlineKeyboardButton(text=use_auto_add_label, callback_data='settings:toggle_use_auto_add')])

    use_original_url_label = _('btn-original-url-on') if ctx.use_original_url else _('btn-original-url')
    rows.append([InlineKeyboardButton(text=use_original_url_label, callback_data='settings:toggle_use_original_url')])

    if ctx.calendar_connected:
        if ctx.selected_calendar:
            cal_label = f'Календарь: {ctx.selected_calendar.calendar_name or ctx.selected_calendar.calendar_id}'
        else:
            cal_label = _('btn-select-calendar')
        rows.append([InlineKeyboardButton(text=cal_label, callback_data='settings:calendar')])

    rows.append([InlineKeyboardButton(text=_('btn-close'), callback_data='settings:close')])

    return InlineKeyboardMarkup(inline_keyboard=rows)
