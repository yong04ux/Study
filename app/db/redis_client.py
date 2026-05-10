"""Redis 客户端工厂。

这个模块提供原始 Redis 连接，适合需要直接操作 Redis 的场景。
如果只是做 JSON 缓存，优先看 app.cache.redis_client.RedisCache。
"""

from redis import Redis

from app.core.config import settings


def get_redis_client() -> Redis:
    """创建 Redis 客户端，用于缓存高频查询结果或读取异步任务状态。"""
    return Redis.from_url(settings.redis_url, decode_responses=True)
