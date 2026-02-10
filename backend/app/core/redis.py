import redis
from app.core.config import get_settings

settings = get_settings()

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=0,
    decode_responses=True,
)

def get_redis():
    return redis_client
