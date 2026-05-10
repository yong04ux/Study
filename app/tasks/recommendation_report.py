"""Kafka-based recommendation report task placeholder."""


async def enqueue_recommendation_report(student_id: str) -> None:
    """
    Placeholder for asynchronous report generation.

    In a full implementation, this function can publish a message to Kafka
    so a background consumer generates a detailed recommendation report.
    """
    _ = student_id
