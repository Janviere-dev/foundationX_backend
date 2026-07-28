#!/usr/bin/env python3

import logging

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import RedisError

from core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class RedisConnection:
    client: Redis = None


redis_connection = RedisConnection()


async def connect_to_redis() -> None:
    logger.info("Connecting to Redis...")

    try:
        redis_connection.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            health_check_interval=30,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            retry=Retry(ExponentialBackoff(cap=10, base=0.5), settings.REDIS_MAX_RETRIES),
            retry_on_error=[ConnectionError, TimeoutError],
            )
        await redis_connection.client.ping()
        logger.info("Redis connection established")
    except (RedisError, ConnectionError, TimeoutError, OSError):
        logger.warning("Redis is unavailable - continuing without cache", exc_info=True)
        redis_connection.client = None


async def close_redis_connection() -> None:
    logger.info("Closing Redis connection...")

    if redis_connection.client:
        await redis_connection.client.close()

    logger.info("Redis connection closed")


def get_redis() -> Redis | None:
    """Returns the shared Redis client, or None if Redis was unavailable"""
    return redis_connection.client
