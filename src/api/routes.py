from typing import Annotated

from aiogram import types
from fastapi import APIRouter, Header, HTTPException
from loguru import logger

from bot import bot, dp
from settings import get_settings

cfg = get_settings()

router = APIRouter(tags=["root"])


@router.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


if cfg.webhook_path:
    @router.post(cfg.webhook_path)
    async def bot_webhook(
        update: dict,
        x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
    ) -> None:
        """ Register webhook endpoint for telegram bot"""
        if x_telegram_bot_api_secret_token != cfg.telegram_my_token:
            logger.error('Wrong secret token')
            raise HTTPException(status_code=401, detail='Wrong secret token')
        telegram_update = types.Update(**update)
        await dp.feed_webhook_update(bot=bot, update=telegram_update)
