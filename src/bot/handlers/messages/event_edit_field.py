from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import t, telegram_router
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
    post_url = event.post_url if field == 'url' else None
    has_value = field in ('location', 'description', 'url') and bool(getattr(event, field))

    await state.set_state(EventEditState.waiting_field_value)
    await state.update_data(
        event_id=event.id,
        field=field,
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
    )
    await query.message.edit_text(
        rich_message=build_edit_field_message(field, getattr(event, field)),
        reply_markup=event_edit_field_keyboard(event.id, field=field, post_url=post_url, has_value=has_value),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:set_post_url:'), EventFilter())
async def cb_set_post_url(query: CallbackQuery, state: FSMContext, session: AsyncSession, event: Event) -> None:
    await state.clear()
    event.url = event.post_url
    await session.commit()
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:clear_field:'), EventFilter())
async def cb_clear_field(query: CallbackQuery, state: FSMContext, session: AsyncSession, event: Event) -> None:
    field = query.data.split(':')[3]
    await state.clear()
    setattr(event, field, None)
    await session.commit()
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.message(EventEditState.waiting_field_value)
async def on_edit_field_value(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    if (event := await get_event(session, data['event_id'])) is None:
        await message.answer(t('event-not-found'))
        return

    setattr(event, data['field'], message.text)
    await session.commit()

    await message.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
    await message.answer_rich(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
