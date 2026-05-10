"""Redis 缓存工具，带有“失败不影响主流程”的降级能力。

设计思路：
1. 高频查询先读 Redis，命中则直接返回，减少 MySQL 压力。
2. Redis 连接失败、超时或 JSON 解析失败时，不抛给业务层，而是返回未命中。
3. 业务层继续查 MySQL，保证“缓存坏了，核心功能仍可用”。
"""

from __future__ import annotations

import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class RedisCache:
    """轻量 JSON 缓存封装，适合缓存院校详情、搜索结果、分数线等数据。"""

    def __init__(self, namespace: str = "gaokao-pilot") -> None:
        # namespace 用于隔离不同模块或不同版本的缓存 key，避免旧数据串用。
        self.namespace = namespace
        self._client: Redis | None = None

    @property
    def client(self) -> Redis:
        """懒加载 Redis 客户端，避免应用启动时强依赖 Redis 已经可用。"""
        if self._client is None:
            self._client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        return self._client

    def build_key(self, *parts: Any) -> str:
        """根据查询参数拼接带命名空间的缓存 key。"""
        safe_parts = [self._normalize_part(part) for part in parts]
        return f"{self.namespace}:" + ":".join(safe_parts)

    def get_json(self, key: str) -> tuple[bool, Any]:
        """
        从 Redis 读取 JSON。

        返回值说明：
        - (False, None)：缓存未命中，或 Redis 暂时不可用。
        - (True, value)：缓存命中，value 可以是普通对象，也可以是缓存的 None。
        """
        try:
            raw_value = self.client.get(key)
            if raw_value is None:
                return False, None
            return True, json.loads(raw_value)
        except (RedisError, OSError, json.JSONDecodeError):
            return False, None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        """把对象序列化为 JSON 写入 Redis；写失败时静默降级。"""
        try:
            self.client.setex(
                key,
                ttl_seconds,
                json.dumps(value, ensure_ascii=False, default=str),
            )
        except (RedisError, OSError, TypeError, ValueError):
            return

    @staticmethod
    def _normalize_part(part: Any) -> str:
        """规范化 key 片段，避免 None、空字符串或空格导致缓存 key 不稳定。"""
        if part is None or part == "":
            return "all"
        return str(part).strip().replace(" ", "_")
