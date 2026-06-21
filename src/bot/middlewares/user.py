from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from db.session import AsyncSessionFactory
from models import User
from models.user_settings import UserSettings


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get('event_from_user')
        if tg_user is None:
            return await handler(event, data)

        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(User)
                .where(User.tg_id == tg_user.id)
                .options(
                    joinedload(User.settings),
                    selectinload(User.oauth_credentials),
                    selectinload(User.calendars),
                )
            )
            db_user = result.scalar_one_or_none()

            if db_user is None:
                db_user = User(
                    tg_id=tg_user.id,
                    tg_username=tg_user.username,
                    tg_full_name=tg_user.full_name,
                    oauth_credentials=[],
                    calendars=[],
                )
                db_user.settings = UserSettings()
                session.add(db_user)
            else:
                db_user.tg_username = tg_user.username
                db_user.tg_full_name = tg_user.full_name

            await session.commit()

            data['db_user'] = db_user
            data['session'] = session
            return await handler(event, data)
