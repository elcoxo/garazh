from datetime import datetime, timezone

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_i18n.lazy import LazyProxy as _
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import my_events_detail_keyboard, my_events_keyboard
from bot.views import build_event_message, build_my_events_message
from models import User
from services.events import list_upcoming_events


async def _render_list(user_id: int, active_idx: int, session: AsyncSession):
    if not (events := await list_upcoming_events(session, user_id, since=datetime.now(timezone.utc))):
        return build_my_events_message(events, 0), None
    active_idx = max(0, min(active_idx, len(events) - 1))
    return build_my_events_message(events, active_idx), my_events_keyboard(active_idx, len(events))


@telegram_router.message(F.text == _('btn-my-events'))
async def btn_my_events(message: Message, db_user: User, session: AsyncSession) -> None:
    rich_message, reply_markup = await _render_list(db_user.id, active_idx=0, session=session)
    await message.answer_rich(rich_message=rich_message, reply_markup=reply_markup)


@telegram_router.callback_query(F.data.startswith('my_events:nav:'))
async def cb_my_events_nav(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    active_idx = int(query.data.split(':')[2])
    rich_message, reply_markup = await _render_list(db_user.id, active_idx=active_idx, session=session)
    await query.message.edit_text(rich_message=rich_message, reply_markup=reply_markup)
    await query.answer()


@telegram_router.callback_query(F.data.startswith('my_events:detail:'))
async def cb_my_events_detail(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    active_idx = int(query.data.split(':')[2])
    if not (events := await list_upcoming_events(session, db_user.id, since=datetime.now(timezone.utc))):
        await query.answer()
        return
    active_idx = max(0, min(active_idx, len(events) - 1))
    await query.message.edit_text(
        rich_message=build_event_message(events[active_idx], title=_('title-event')),
        reply_markup=my_events_detail_keyboard(active_idx),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('my_events:back:'))
async def cb_my_events_back(query: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    active_idx = int(query.data.split(':')[2])
    rich_message, reply_markup = await _render_list(db_user.id, active_idx=active_idx, session=session)
    await query.message.edit_text(rich_message=rich_message, reply_markup=reply_markup)
    await query.answer()


@telegram_router.callback_query(F.data == 'my_events:noop')
async def cb_my_events_noop(query: CallbackQuery) -> None:
    await query.answer()
