from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram_i18n import I18nContext
from aiogram_i18n.lazy import LazyProxy as _
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.filters import EventFilter
from bot.keyboards import UserContext, event_added_keyboard, event_edit_keyboard, event_preview_keyboard, main_keyboard
from bot.views import EDIT_EVENT_FOOTER, EDIT_EVENT_TITLE, build_event_message
from models import Event, User
from services.calendar import CalendarAuthError, CalendarError
from services.events import SyncOutcome, get_user_event, remove_event_from_calendar, sync_event_to_calendar

EMPTY_MARKUP = InlineKeyboardMarkup(inline_keyboard=[])

FOOTER_BY_SYNC = {
    SyncOutcome.CREATED: _('footer-sync-created'),
    SyncOutcome.UPDATED: _('footer-sync-updated'),
}


async def _handle_auth_error(query: CallbackQuery, restore_markup: InlineKeyboardMarkup, db_user: User) -> None:
    ctx = UserContext(
        calendar_connected=False,
        use_auto_add=db_user.settings.use_auto_add if db_user.settings else False,
    )
    await query.message.edit_reply_markup(reply_markup=restore_markup)
    await query.message.answer(_('auth-revoked'), reply_markup=main_keyboard(ctx))
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:add:'), EventFilter())
async def cb_add(query: CallbackQuery, db_user: User, session: AsyncSession, event: Event, i18n: I18nContext) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    try:
        outcome = await sync_event_to_calendar(session, db_user, event)
    except CalendarAuthError:
        await _handle_auth_error(query, event_preview_keyboard(event.id), db_user)
        return
    except CalendarError as e:
        await query.message.edit_text(i18n.get('calendar-add-failed', error=str(e)))
        await query.answer()
        return

    if outcome == SyncOutcome.NO_CALENDAR:
        await query.answer(i18n.get('no-cal-selected'))
        return

    await query.message.edit_text(
        rich_message=build_event_message(
            event, title=_('title-new-event'), footer=FOOTER_BY_SYNC[outcome], compact=True,
        ),
        reply_markup=event_added_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:cancel:'))
async def cb_cancel(query: CallbackQuery) -> None:
    await query.message.delete()
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit:'), EventFilter())
async def cb_edit(query: CallbackQuery, event: Event) -> None:
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_back:'), EventFilter())
async def cb_edit_back(query: CallbackQuery, event: Event) -> None:
    await query.message.edit_text(
        rich_message=build_event_message(event, title=_('title-new-event')),
        reply_markup=event_preview_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_save:'), EventFilter())
async def cb_edit_save(
    query: CallbackQuery, db_user: User, session: AsyncSession, event: Event, i18n: I18nContext,
) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    user_event = await get_user_event(session, db_user.id, event.id)

    if user_event is None:
        await query.message.edit_text(
            rich_message=build_event_message(event, title=_('title-new-event')),
            reply_markup=event_preview_keyboard(event.id),
        )
        await query.answer()
        return

    try:
        outcome = await sync_event_to_calendar(session, db_user, event)
    except CalendarAuthError:
        await _handle_auth_error(query, event_added_keyboard(event.id), db_user)
        return
    except CalendarError as e:
        await query.message.edit_text(
            rich_message=build_event_message(event, title=_('title-event')),
            reply_markup=event_added_keyboard(event.id),
        )
        await query.answer(i18n.get('calendar-add-failed', error=str(e)))
        return

    await query.message.edit_text(
        rich_message=build_event_message(
            event, title=_('title-event'), footer=FOOTER_BY_SYNC.get(outcome), compact=True,
        ),
        reply_markup=event_added_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:remove:'), EventFilter())
async def cb_remove(
    query: CallbackQuery, db_user: User, session: AsyncSession, event: Event, i18n: I18nContext,
) -> None:
    await query.message.edit_reply_markup(reply_markup=EMPTY_MARKUP)

    try:
        removed = await remove_event_from_calendar(session, db_user.id, event)
    except CalendarAuthError:
        await _handle_auth_error(query, event_added_keyboard(event.id), db_user)
        return
    except CalendarError as e:
        await query.message.edit_text(i18n.get('calendar-remove-failed', error=str(e)))
        await query.answer()
        return

    if not removed:
        await query.answer(i18n.get('event-not-in-calendar'))
        return

    await query.message.delete()
    await query.answer(i18n.get('event-removed'))
