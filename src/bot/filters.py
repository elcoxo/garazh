from aiogram.filters import Filter
from aiogram.types import CallbackQuery
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.events import get_event


class EventFilter(Filter):
    async def __call__(self, query: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> dict | bool:
        if (event := await get_event(session, int(query.data.split(':')[2]))) is None:
            await query.answer(i18n.get('event-not-found'), show_alert=True)
            return False
        return {'event': event}
