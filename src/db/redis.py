from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from settings import get_settings

cfg = get_settings()

pool = ConnectionPool.from_url(cfg.redis_url)
redis_client = Redis(connection_pool=pool)
