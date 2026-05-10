"""Kafka Producer 工厂。

Kafka 用于处理耗时较长的异步任务，例如志愿推荐报告生成。
API 请求只负责投递任务，真正的报告生成由 Consumer 在后台完成。
"""

from aiokafka import AIOKafkaProducer

from app.core.config import settings


def get_kafka_producer() -> AIOKafkaProducer:
    """创建异步 Kafka Producer，用来向报告任务 Topic 发送消息。"""
    return AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
