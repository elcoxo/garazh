import asyncio
from logging.config import fileConfig

from sqlalchemy import String, Text, pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy_utils import StringEncryptedType
from alembic import context

from settings import get_settings
from models.base import Base
import models  # noqa: F401

# import models.user  # noqa
# import models.oauth_credential  # noqa
# import models.caldav_credential  # noqa
# import models.user_calendar  # noqa

config = context.config
cfg = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    if type_ == "type" and obj.__class__.__name__ == "StringEncryptedType":
        return "sa.Text()"
    return False


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    if isinstance(metadata_type, StringEncryptedType) and isinstance(inspected_type, (Text, String)):
        return False
    return None


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=compare_type,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(cfg.database_url, poolclass=pool.NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=cfg.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
