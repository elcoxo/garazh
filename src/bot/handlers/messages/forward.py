from aiogram import F
from aiogram.types import (
    InputRichMessage,
    Message,
    MessageOriginChannel,
    MessageOriginChat,
)
from aiogram_i18n import I18nContext
from aiogram_i18n.lazy import LazyProxy as _
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


@telegram_router.message(F.forward_origin)
async def handle_forward(message: Message, db_user: User, session: AsyncSession, i18n: I18nContext) -> None:
    origin = message.forward_origin
    text = message.text or message.caption

    if not isinstance(origin, (MessageOriginChannel, MessageOriginChat)):
        await message.answer(_('forward-unsupported'))
        return

    if not text:
        if message.media_group_id is not None:
            return
        await message.answer(_('forward-no-text'))
        return

    if db_user.calendar is None:
        await message.answer(_('connect-calendar-first'))
        return

    await message.bot.send_rich_message_draft(
        chat_id=message.chat.id,
        draft_id=message.message_id,
        rich_message=InputRichMessage(html=f'<tg-thinking>{_("extracting")}</tg-thinking>'),
    )
    post = ForwardInput.from_message(origin, text, message)
    result = await process_forward_post(session, post, user_id=db_user.id)

    await _send_forward_result(message, db_user, result, session, i18n)


async def _send_forward_result(
        message: Message,
        db_user: User,
        result: ForwardResult,
        session: AsyncSession,
        i18n: I18nContext,
) -> None:
    if (
        result.outcome == ForwardOutcome.EXTRACTED
        and not result.event.url
        and db_user.settings
        and db_user.settings.use_original_url
    ):
        result.event.url = result.event.post_url

    match result.outcome:
        case ForwardOutcome.AI_DISABLED:
            await message.answer_rich(rich_message=InputRichMessage(markdown=_('ai-disabled')))
        case ForwardOutcome.NO_EVENT:
            await message.answer_rich(rich_message=InputRichMessage(markdown=_('no-event-found')))
        case ForwardOutcome.DUPLICATE:
            await message.answer_rich(
                rich_message=build_event_message(
                    result.event, title=_('title-event'), footer=_('footer-already-in-calendar'), compact=True,
                ),
                reply_markup=event_added_keyboard(result.event.id),
            )
        case ForwardOutcome.EXTRACTED if db_user.settings.use_auto_add:
            try:
                outcome = await sync_event_to_calendar(session, db_user, result.event)
            except CalendarError as e:
                await message.answer_rich(rich_message=InputRichMessage(markdown=i18n.get('calendar-add-failed', error=str(e))))
                return
            if outcome == SyncOutcome.NO_CALENDAR:
                await message.answer_rich(rich_message=InputRichMessage(markdown=_('no-cal-selected')))
                return
            await message.answer_rich(
                rich_message=build_event_message(
                    result.event, title=_('title-event'), footer=_('footer-sync-created'), compact=True,
                ),
                reply_markup=event_added_keyboard(result.event.id),
            )
        case ForwardOutcome.EXTRACTED:
            await message.answer_rich(
                rich_message=build_event_message(result.event, title=_('title-new-event')),
                reply_markup=event_preview_keyboard(result.event.id),
            )
