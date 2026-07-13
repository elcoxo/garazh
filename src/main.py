from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

import bot.handlers  # noqa
from api import auth, routes
from settings import get_settings

cfg = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    from bot import start_telegram, stop_telegram
    logger.info('🚀 Starting application')
    await start_telegram()
    yield
    await stop_telegram()
    logger.info('⛔ Stopping application')

app = FastAPI(lifespan=lifespan)
app.include_router(routes.router)
app.include_router(auth.router)
