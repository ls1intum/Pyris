from redis import Redis
from app.config import settings

cache_store = Redis(
    host=settings.pyris.redis.host,
    port=settings.pyris.redis.port,
    decode_responses=True,
)
