from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

import handlers # noqa, get handlers for Telegram
from routes import root_router
from settings import get_settings

cfg = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    from bot import start_telegram, stop_telegram
    logger.info("🚀 Starting application")
    await start_telegram()
    yield
    await stop_telegram()
    logger.info("⛔ Stopping application")

app = FastAPI(lifespan=lifespan)
app.include_router(root_router)
