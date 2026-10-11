import os
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from settings import get_settings

cfg = get_settings()

if os.getenv('VERCEL'):
    engine = create_async_engine(
        cfg.database_url,
        echo=cfg.debug,
        poolclass=NullPool,
        connect_args={'statement_cache_size': 0, 'prepared_statement_cache_size': 0},
    )
else:
    engine = create_async_engine(cfg.database_url, echo=cfg.debug)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
