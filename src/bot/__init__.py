import asyncio
from datetime import timedelta

import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import WebhookInfo, BotCommand

from loguru import logger

# from system import first_run
from settings import get_settings, Settings
from bot.middlewares import UserMiddleware
from db.redis import pool

cfg: Settings = get_settings()

telegram_router = Router(name="telegram")
storage = RedisStorage(
    redis=aioredis.Redis(connection_pool=pool),
    state_ttl=timedelta(hours=24),
    data_ttl=timedelta(hours=24),
)
dp = Dispatcher(storage=storage)

dp.update.middleware(UserMiddleware())
dp.include_router(telegram_router)
bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

_polling_task: asyncio.Task | None = None


async def set_bot_commands(my_bot: Bot) -> None:
    commands = [
        BotCommand(command='/start', description='Запустить бота'),
        BotCommand(command='/connect', description='Подключить Google Calendar'),
        BotCommand(command='/calendars', description='Список календарей'),
        BotCommand(command="/id", description="👋 Get my ID"),
    ]
    try:
        await my_bot.set_my_commands(commands)
    except Exception as e:
        logger.error(f"Can't set commands - {e}")


async def _setup_webhook() -> None:
    async def check_webhook() -> WebhookInfo | None:
        try:
            return await bot.get_webhook_info()
        except Exception as e:
            logger.error(f"Can't get webhook info - {e}")

    current = await check_webhook()
    try:
        await bot.set_webhook(
            f"{cfg.base_webhook_url}{cfg.webhook_path}",
            secret_token=cfg.telegram_my_token,
            drop_pending_updates=bool(current and current.pending_update_count > 0),
            max_connections=100,
        )
    except Exception as e:
        logger.error(f"Can't set webhook - {e}")


async def start_telegram() -> None:
    await set_bot_commands(bot)

    if cfg.debug:
        await bot.delete_webhook(drop_pending_updates=True)
        global _polling_task
        _polling_task = asyncio.create_task(dp.start_polling(bot))
        logger.info("Bot started in polling mode")
    else:
        await _setup_webhook()
        logger.info("Bot started in webhook mode")


async def stop_telegram() -> None:
    if _polling_task:
        await dp.stop_polling()
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass

# async def start_telegram():
#     fr = await first_run()
#     if cfg.debug:
#         logger.debug(f"First run: {fr}")
#     if fr:
#         await set_webhook(bot)
#         await set_bot_commands_menu(bot)
