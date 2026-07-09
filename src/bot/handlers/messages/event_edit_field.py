from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import event_edit_field_keyboard, event_edit_keyboard
from bot.views import EDIT_EVENT_FOOTER, EDIT_EVENT_TITLE, build_edit_field_message, build_event_message
from services.events import get_event

MSG_EVENT_NOT_FOUND = 'Событие не найдено'


class EventEditState(StatesGroup):
    waiting_field_value = State()


@telegram_router.callback_query(F.data.startswith('event:edit_field_cancel:'))
async def cb_edit_field_cancel(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    event = await get_event(session, int(query.data.split(':')[2]))
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    await state.clear()
    await query.message.edit_text(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
    await query.answer()


@telegram_router.callback_query(F.data.startswith('event:edit_field:'))
async def cb_edit_field(query: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    parts = query.data.split(':')
    event_id = int(parts[2])
    field = parts[3]

    event = await get_event(session, event_id)
    if event is None:
        await query.answer(MSG_EVENT_NOT_FOUND, show_alert=True)
        return

    await state.set_state(EventEditState.waiting_field_value)
    await state.update_data(
        event_id=event_id,
        field=field,
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
    )
    await query.message.edit_text(
        rich_message=build_edit_field_message(field, getattr(event, field)),
        reply_markup=event_edit_field_keyboard(event_id),
    )
    await query.answer()


@telegram_router.message(EventEditState.waiting_field_value)
async def on_edit_field_value(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    event = await get_event(session, data['event_id'])
    if event is None:
        await message.answer(MSG_EVENT_NOT_FOUND)
        return

    setattr(event, data['field'], message.text)
    await session.commit()

    await message.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
    await message.answer_rich(
        rich_message=build_event_message(event, title=EDIT_EVENT_TITLE, footer=EDIT_EVENT_FOOTER),
        reply_markup=event_edit_keyboard(event.id),
    )
