from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import event_added_keyboard, event_edit_keyboard, event_preview_keyboard
from bot.views import EDIT_EVENT_FOOTER, EDIT_EVENT_TITLE, build_event_message
from models import User
from services.calendar.exceptions import CalendarError
from services.events import SyncOutcome, get_event, remove_event_from_calendar, sync_event_to_calendar

MSG_EVENT_NOT_FOUND = 'Событие не найдено'
MSG_NO_CAL_SELECTED = 'Сначала выбери календарь'
MSG_CALENDAR_FAILED = '⚠️ Не удалось добавить в календарь: {error}'
MSG_REMOVE_FAILED = '⚠️ Не удалось удалить из календаря: {error}'

EMPTY_MARKUP = InlineKeyboardMarkup(inline_keyboard=[])

FOOTER_BY_SYNC = {
    SyncOutcome.CREATED: '✅ Добавлено в календарь!',
    SyncOutcome.UPDATED: '✅ Обновлено в календаре!',
}


@telegram_router.callback_query(F.data.startswith('event:add:'))
async def cb_add(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    try:
        outcome = await sync_event_to_calendar(session, db_user, event)
    except CalendarError as e:
        await query.message.edit_text(MSG_CALENDAR_FAILED.format(error=e))
        await query.answer()
        return

    if outcome == SyncOutcome.NO_CALENDAR:
        await query.answer(MSG_NO_CAL_SELECTED, show_alert=True)
        return

    await query.message.edit_text(
        rich_message=build_event_message(
            event, title='Новое событие', footer=FOOTER_BY_SYNC[outcome], compact=True,
        ),
        reply_markup=event_added_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:cancel:'))
async def cb_cancel(query: CallbackQuery) -> None:
    await query.message.delete()
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit:'))
async def cb_edit(query: CallbackQuery, session: AsyncSession) -> None:
    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_back:'))
async def cb_edit_back(query: CallbackQuery, session: AsyncSession) -> None:
    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    await query.message.edit_text(
        rich_message=build_event_message(event, title='Новое событие'),
        reply_markup=event_preview_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_save:'))
async def cb_edit_save(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    try:
        outcome = await sync_event_to_calendar(session, db_user, event)
    except CalendarError as e:
        await query.message.edit_text(MSG_CALENDAR_FAILED.format(error=e))
        await query.answer()
        return

    if outcome == SyncOutcome.NO_CALENDAR:
        await query.answer(MSG_NO_CAL_SELECTED, show_alert=True)
        return

    await query.message.edit_text(
        rich_message=build_event_message(
            event, title='Событие', footer=FOOTER_BY_SYNC[outcome], compact=True,
        ),
        reply_markup=event_added_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:remove:'))
async def cb_remove(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    try:
        removed = await remove_event_from_calendar(session, db_user.id, event)
    except CalendarError as e:
        await query.message.edit_text(MSG_REMOVE_FAILED.format(error=e))
        await query.answer()
        return

    if not removed:
        await query.answer('Событие не было в календаре', show_alert=True)
        return

    await query.message.delete()
    await query.answer('Удалено из календаря')
