from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_i18n.lazy import LazyProxy as _
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.filters import EventFilter
from bot.keyboards import event_edit_field_keyboard, event_edit_keyboard
from bot.views import EDIT_EVENT_FOOTER, EDIT_EVENT_TITLE, build_edit_field_message, build_event_message
from models import Event
from services.events import get_event


class EventEditState(StatesGroup):
    waiting_field_value = State()


@telegram_router.callback_query(F.data.startswith('event:edit_field_cancel:'), EventFilter())
async def cb_edit_field_cancel(query: CallbackQuery, state: FSMContext, event: Event) -> None:
    await state.clear()
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_field:'), EventFilter())
async def cb_edit_field(query: CallbackQuery, state: FSMContext, event: Event) -> None:
    field = query.data.split(':')[3]

    await state.set_state(EventEditState.waiting_field_value)
    await state.update_data(
        event_id=event.id,
        field=field,
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
    )
    await query.message.edit_text(
        rich_message=build_edit_field_message(field, getattr(event, field)),
        reply_markup=event_edit_field_keyboard(event.id),
    )
    await query.answer()


@telegram_router.message(EventEditState.waiting_field_value)
async def on_edit_field_value(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    event = await get_event(session, data['event_id'])
    if event is None:
        await message.answer(_('event-not-found'))
        return

    setattr(event, data['field'], message.text)
    await session.commit()

    await message.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
    await message.answer_rich(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
