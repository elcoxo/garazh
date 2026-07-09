from aiogram import F
from aiogram.types import (
    InputRichMessage,
    Message,
    MessageOriginChannel,
    MessageOriginChat,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot import telegram_router
from bot.keyboards import event_added_keyboard, event_preview_keyboard
from bot.views import build_event_message
from models import User
from services.calendar.exceptions import CalendarError
from services.events import (
    ForwardInput,
    ForwardOutcome,
    ForwardResult,
    SyncOutcome,
    process_forward_post,
    sync_event_to_calendar,
)

MSG_UNSUPPORTED = 'Поддерживаются только пересылки из каналов и групп'
MSG_NO_TEXT = 'Перешли пост с текстом, нужно описание события'
MSG_NO_CALENDAR = 'Сначала подключи календарь'
MSG_EXTRACTING = '🫥 Кумекаю...'
MSG_AI_DISABLED = 'AI временно отключён'
MSG_NO_EVENT = '🤷 Не нашёл событие в этом посте'
MSG_NO_CAL_SELECTED = 'Сначала выбери календарь'
MSG_CALENDAR_FAILED = '⚠️ Не удалось добавить в календарь: {error}'


@telegram_router.message(F.forward_origin)
async def handle_forward(message: Message, db_user: User, session: AsyncSession) -> None:
    origin = message.forward_origin
    text = message.text or message.caption

    if not isinstance(origin, (MessageOriginChannel, MessageOriginChat)):
        await message.answer(MSG_UNSUPPORTED)
        return

    if not text:
        if message.media_group_id is not None:
            return
        await message.answer(MSG_NO_TEXT)
        return

    if db_user.calendar is None:
        await message.answer(MSG_NO_CALENDAR)
        return

    await message.bot.send_rich_message_draft(
        chat_id=message.chat.id,
        draft_id=message.message_id,
        rich_message=InputRichMessage(html=f'<tg-thinking>{MSG_EXTRACTING}</tg-thinking>'),
    )
    post = ForwardInput.from_message(origin, text, message)
    result = await process_forward_post(session, post, user_id=db_user.id)

    await _send_forward_result(message, db_user, result, session)


async def _send_forward_result(
        message: Message,
        db_user: User,
        result: ForwardResult,
        session: AsyncSession,
) -> None:
    match result.outcome:
        case ForwardOutcome.AI_DISABLED:
            await message.answer_rich(rich_message=InputRichMessage(markdown=MSG_AI_DISABLED))
        case ForwardOutcome.NO_EVENT:
            await message.answer_rich(rich_message=InputRichMessage(markdown=MSG_NO_EVENT))
        case ForwardOutcome.DUPLICATE:
            await message.answer_rich(
                rich_message=build_event_message(
                    result.event, title='Событие', footer='✅ Уже в календаре', compact=True,
                ),
                reply_markup=event_added_keyboard(result.event.id),
            )
        case ForwardOutcome.EXTRACTED if db_user.settings.auto_add:
            try:
                outcome = await sync_event_to_calendar(session, db_user, result.event)
            except CalendarError as e:
                await message.answer_rich(rich_message=InputRichMessage(markdown=MSG_CALENDAR_FAILED.format(error=e)))
                return
            if outcome == SyncOutcome.NO_CALENDAR:
                await message.answer_rich(rich_message=InputRichMessage(markdown=MSG_NO_CAL_SELECTED))
                return
            await message.answer_rich(
                rich_message=build_event_message(
                    result.event, title='Событие', footer='✅ Добавлено в календарь!', compact=True,
                ),
                reply_markup=event_added_keyboard(result.event.id),
            )
        case ForwardOutcome.EXTRACTED:
            await message.answer_rich(
                rich_message=build_event_message(result.event, title='Новое событие'),
                reply_markup=event_preview_keyboard(result.event.id),
            )
