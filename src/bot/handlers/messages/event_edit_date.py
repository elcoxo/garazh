from datetime import datetime, timedelta

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.filters import EventFilter
from bot.keyboards import (
    event_date_end_keyboard,
    event_date_keyboard,
    event_date_start_keyboard,
    event_edit_keyboard,
)
from bot.views import EDIT_EVENT_FOOTER, EDIT_EVENT_TITLE, EventView, build_event_message
from models import Event
from services.events import get_event


class EventDateEditState(StatesGroup):
    editing = State()


async def _render_staged_date_screen(
        query: CallbackQuery,
        event: Event,
        data: dict,
        keyboard: InlineKeyboardMarkup,
) -> None:
    await query.message.edit_text(
        rich_message=build_event_message(
            EventView.with_date_state(event, data),
            title=EDIT_EVENT_TITLE,
            footer=EDIT_EVENT_FOOTER,
        ),
        reply_markup=keyboard,
    )
    await query.answer()


async def _render_edit_menu(query: CallbackQuery, event: Event) -> None:
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:date_open:'), EventFilter())
async def cb_date_open(query: CallbackQuery, state: FSMContext, event: Event) -> None:
    data = {
        'event_id': event.id,
        'all_day': event.all_day,
        'dtstart_iso': event.dtstart.isoformat(),
        'dtend_iso': event.dtend.isoformat() if event.dtend else None,
    }
    await state.set_state(EventDateEditState.editing)
    await state.set_data(data)
    await _render_staged_date_screen(query, event, data, event_date_keyboard(event.id, data['all_day']))


@telegram_router.callback_query(F.data.startswith('event:date_toggle_allday:'), EventDateEditState.editing)
async def cb_date_toggle_allday(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    prev = await state.get_data()
    data = await state.update_data(all_day=not prev['all_day'])
    event = await get_event(session, data['event_id'])
    await _render_staged_date_screen(query, event, data, event_date_keyboard(event.id, data['all_day']))


@telegram_router.callback_query(F.data.startswith('event:date_show_start:'), EventDateEditState.editing)
async def cb_date_show_start(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    event = await get_event(session, data['event_id'])
    await _render_staged_date_screen(query, event, data, event_date_start_keyboard(event.id))


@telegram_router.callback_query(F.data.startswith('event:date_show_end:'), EventDateEditState.editing)
async def cb_date_show_end(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    event = await get_event(session, data['event_id'])
    dtstart = datetime.fromisoformat(data['dtstart_iso'])
    await _render_staged_date_screen(query, event, data, event_date_end_keyboard(event.id, dtstart))


@telegram_router.callback_query(F.data.startswith('event:date_pick_start:'), EventDateEditState.editing)
async def cb_date_pick_start(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    hhmm = query.data.split(':')[3]
    h, m = int(hhmm[:2]), int(hhmm[2:])

    prev = await state.get_data()
    dtstart = datetime.fromisoformat(prev['dtstart_iso']).replace(hour=h, minute=m)
    data = await state.update_data(dtstart_iso=dtstart.isoformat())

    event = await get_event(session, data['event_id'])
    await _render_staged_date_screen(query, event, data, event_date_keyboard(event.id, data['all_day']))


@telegram_router.callback_query(F.data.startswith('event:date_pick_end:'), EventDateEditState.editing)
async def cb_date_pick_end(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    offset = int(query.data.split(':')[3])

    prev = await state.get_data()
    dtstart = datetime.fromisoformat(prev['dtstart_iso'])
    dtend = dtstart + timedelta(hours=offset)
    data = await state.update_data(dtend_iso=dtend.isoformat())

    event = await get_event(session, data['event_id'])
    await _render_staged_date_screen(query, event, data, event_date_keyboard(event.id, data['all_day']))


@telegram_router.callback_query(F.data.startswith('event:date_manual:'), EventDateEditState.editing)
async def cb_date_manual_input(query: CallbackQuery) -> None:
    await query.answer('WIP', show_alert=True)


@telegram_router.callback_query(F.data.startswith('event:date_picker_back:'), EventDateEditState.editing)
async def cb_date_picker_back(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    event = await get_event(session, data['event_id'])
    await _render_staged_date_screen(query, event, data, event_date_keyboard(event.id, data['all_day']))


@telegram_router.callback_query(F.data.startswith('event:date_save:'), EventDateEditState.editing)
async def cb_date_save(query: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext) -> None:
    data = await state.get_data()

    if not data['all_day'] and not data.get('dtend_iso'):
        await query.answer(i18n.get('dtend-required'), show_alert=True)
        return

    if (event := await get_event(session, data['event_id'])) is None:
        await state.clear()
        await query.answer(i18n.get('event-not-found'), show_alert=True)
        return

    event.all_day = data['all_day']
    event.dtstart = datetime.fromisoformat(data['dtstart_iso'])
    event.dtend = None if data['all_day'] else datetime.fromisoformat(data['dtend_iso'])
    await session.commit()
    await state.clear()

    await _render_edit_menu(query, event)


@telegram_router.callback_query(F.data.startswith('event:date_cancel:'), EventDateEditState.editing)
async def cb_date_cancel(query: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext) -> None:
    event = await get_event(session, int(query.data.split(':')[2]))
    await state.clear()
    if event is None:
        await query.answer(i18n.get('event-not-found'), show_alert=True)
        return
    await _render_edit_menu(query, event)
