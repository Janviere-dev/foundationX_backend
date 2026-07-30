#!/usr/bin/env python3

import logging
from typing import Optional

from core.config import get_settings
from db.redis.setup import get_redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "student_profile:"


def _key(user_id: str) -> str:
    return f"{_KEY_PREFIX}{user_id}"


async def cache_student_profile(user_id: str, profile_json: str) -> None:
    client = get_redis()
    if client is None:
        logger.warning("Redis unavailable - skipping profile cache for user_id=%s", user_id)
        return
    ttl_seconds = get_settings().STUDENT_PROFILE_CACHE_MINUTES * 60
    await client.set(_key(user_id), profile_json, ex=ttl_seconds)


async def get_cached_student_profile(user_id: str) -> Optional[str]:
    client = get_redis()
    if client is None:
        return None
    return await client.get(_key(user_id))


async def invalidate_cached_student_profile(user_id: str) -> None:
    client = get_redis()
    if client is None:
        return
    await client.delete(_key(user_id))
