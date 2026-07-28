#!/usr/bin/env python3

import logging
from typing import Optional

from core.config import get_settings
from db.redis.setup import get_redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "learning_content:"


def _key(content_id: str) -> str:
    return f"{_KEY_PREFIX}{content_id}"


async def cache_learning_content(content_id: str, document_json: str) -> None:
    """Cache a generated lesson in Redis as a read accelerator. Unlike the
    quiz cache, this TTL is pure cache hygiene, not a business signal - a
    student can resume a lesson at their own pace indefinitely, since
    MongoDB (not this cache) is the permanent, authoritative copy. A cache
    miss just means "read Mongo and repopulate", never "the lesson is gone".
    """
    client = get_redis()
    if client is None:
        logger.warning("Redis unavailable - skipping lesson cache for content_id=%s", content_id)
        return
    ttl_seconds = get_settings().LEARNING_CONTENT_EXPIRE_MINUTES * 60
    await client.set(_key(content_id), document_json, ex=ttl_seconds)


async def get_cached_learning_content(content_id: str) -> Optional[str]:
    """Fetch the cached lesson document, if present. Returns None on a
    cache miss (expired, evicted, or Redis unavailable) - callers should
    fall back to MongoDB, not treat this as an error."""
    client = get_redis()
    if client is None:
        return None
    return await client.get(_key(content_id))


async def invalidate_cached_learning_content(content_id: str) -> None:
    """Drop the cached copy so the next read repopulates it from MongoDB -
    used after updating the lesson (e.g. marking it complete) so the cache
    doesn't serve stale data."""
    client = get_redis()
    if client is None:
        return
    await client.delete(_key(content_id))
