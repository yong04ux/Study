"""Kafka Producer：用于提交异步志愿推荐报告任务。

API 层调用 publish_report_task 后，任务会被发送到 Kafka。
这样接口可以立即返回 task_id，不需要等待报告完整生成。
"""

from __future__ import annotations

import json
from typing import Any

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
except Exception:  # pragma: no cover - fallback for environments without aiokafka installed
    AIOKafkaProducer = None  # type: ignore[assignment]

    class KafkaError(RuntimeError):
        """当 aiokafka 未安装时使用的兜底 Kafka 异常类型。"""

from app.core.config import settings

REPORT_TOPIC = settings.kafka_recommendation_topic


class KafkaProducerUnavailable(RuntimeError):
    """Kafka 不可用或无法接收报告任务时抛出的业务异常。"""


async def publish_report_task(payload: dict[str, Any]) -> None:
    """向 Kafka 发布一条报告生成任务。

    业务流程：
    1. 创建 AIOKafkaProducer。
    2. 将 payload 序列化为 JSON bytes。
    3. 发送到 gaokao_recommendation_report topic。
    4. 无论成功失败都尝试关闭 producer，避免连接泄漏。
    """
    if AIOKafkaProducer is None:
        raise KafkaProducerUnavailable("未安装 aiokafka，无法提交 Kafka 报告任务。")

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )

    try:
        await producer.start()
        await producer.send_and_wait(REPORT_TOPIC, payload)
    except (KafkaError, OSError) as exc:
        raise KafkaProducerUnavailable("Kafka 不可用，请检查 Kafka 服务和 Topic 配置。") from exc
    finally:
        try:
            await producer.stop()
        except Exception:
            pass
