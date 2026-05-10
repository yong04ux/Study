"""Kafka Consumer：后台生成异步志愿推荐报告。

运行方式：python -m app.mq.kafka_consumer
它会持续监听报告任务 topic，消费任务后调用 RecommendationService，
并把 processing / completed / failed 状态写入 Redis。
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from aiokafka import AIOKafkaConsumer
    from aiokafka.errors import KafkaError
except Exception:  # pragma: no cover - fallback for environments without aiokafka installed
    AIOKafkaConsumer = None  # type: ignore[assignment]

    class KafkaError(RuntimeError):
        """当 aiokafka 未安装时使用的兜底 Kafka 异常类型。"""

try:
    from redis import Redis
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - fallback for environments without redis installed
    Redis = Any  # type: ignore[assignment]

    class RedisError(RuntimeError):
        """当 redis-py 未安装或 Redis 操作失败时使用的兜底异常类型。"""

from app.core.config import settings
from app.mq.kafka_producer import REPORT_TOPIC
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)
REPORT_TTL_SECONDS = 24 * 60 * 60


def save_report(redis_client: Redis, task_id: str, payload: dict[str, Any]) -> None:
    """把报告状态或最终结果写入 Redis，key 格式为 report:{task_id}。"""
    redis_client.setex(
        f"report:{task_id}",
        REPORT_TTL_SECONDS,
        json.dumps(payload, ensure_ascii=False, default=str),
    )


async def build_report_result(
    recommendation_service: RecommendationService,
    task: dict[str, Any],
) -> dict[str, Any]:
    """复用同步推荐服务生成报告，保证异步报告和页面推荐结果结构一致。"""
    return await recommendation_service.recommend(
        user_id=str(task["user_id"]).strip(),
        province=str(task["province"]).strip(),
        subject_type=str(task["subject_type"]).strip(),
        score=int(task["score"]),
        rank=int(task["rank"]),
        preferred_provinces=[
            str(item).strip()
            for item in task.get("preferred_provinces", [])
            if str(item).strip()
        ],
        preferred_majors=[
            str(item).strip()
            for item in task.get("preferred_majors", [])
            if str(item).strip()
        ],
    )


async def handle_task(
    redis_client: Redis,
    recommendation_service: RecommendationService,
    task: dict[str, Any],
) -> None:
    """处理单个 Kafka 任务：写入 processing，生成报告，再写入 completed 或 failed。"""
    task_id = str(task["task_id"])
    logger.info("Start recommendation report task_id=%s user_id=%s", task_id, task.get("user_id"))

    try:
        save_report(redis_client, task_id, {"task_id": task_id, "status": "processing", "result": None})
        report_result = await build_report_result(recommendation_service, task)
        save_report(redis_client, task_id, {"task_id": task_id, "status": "completed", "result": report_result})
        logger.info("Completed recommendation report task_id=%s", task_id)
    except Exception as exc:
        logger.exception("Failed recommendation report task_id=%s", task_id)
        try:
            save_report(
                redis_client,
                task_id,
                {
                    "task_id": task_id,
                    "status": "failed",
                    "result": None,
                    "error": str(exc),
                },
            )
        except RedisError:
            logger.exception("Failed to write failed status to Redis task_id=%s", task_id)


async def consume_report_tasks() -> None:
    """持续消费 Kafka 报告任务。

    这是一个长运行后台进程：
    1. 初始化 Redis、RecommendationService 和 Kafka Consumer。
    2. 循环读取 Kafka 消息。
    3. 每条消息交给 handle_task 生成报告。
    4. 进程退出时关闭 Kafka Consumer 和 Redis 连接。
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    logger.info("Starting Kafka consumer topic=%s bootstrap=%s", REPORT_TOPIC, settings.kafka_bootstrap_servers)

    if AIOKafkaConsumer is None:
        raise RuntimeError("未安装 aiokafka，无法启动 Kafka Consumer。")
    if not hasattr(Redis, "from_url"):
        raise RuntimeError("未安装 Redis Python 客户端，无法写入报告状态。")

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    recommendation_service = RecommendationService()
    consumer = AIOKafkaConsumer(
        REPORT_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="gaokao-recommendation-report-workers",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        enable_auto_commit=True,
    )

    try:
        await consumer.start()
        async for message in consumer:
            logger.info("Received report task offset=%s partition=%s", message.offset, message.partition)
            await handle_task(redis_client, recommendation_service, message.value)
    except (KafkaError, OSError):
        logger.exception("Kafka consumer stopped because Kafka is unavailable.")
        raise
    finally:
        await consumer.stop()
        redis_client.close()


def main() -> None:
    """命令行入口，用于启动 Kafka Consumer。"""
    asyncio.run(consume_report_tasks())


if __name__ == "__main__":
    main()
