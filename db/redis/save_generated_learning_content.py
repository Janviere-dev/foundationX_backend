#!/usr/bin/env python3

import hashlib
import logging
from typing import Optional

from core.config import get_settings
from db.redis.setup import get_redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "learning_content:"
_LOOKUP_PREFIX = "learning_content_lookup:"


def _key(content_id: str) -> str:
    return f"{_KEY_PREFIX}{content_id}"


def _lookup_key(user_id: str, subject: str, learning_query: str, grade: str) -> str:
    raw = f"{user_id}:{subject}:{learning_query}:{grade}".lower()
    return f"{_LOOKUP_PREFIX}{hashlib.sha256(raw.encode()).hexdigest()}"


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


async def cache_content_lookup(user_id: str, subject: str, learning_query: str, grade: str, content_id: str) -> None:
    client = get_redis()
    if client is None:
        return
    ttl_seconds = get_settings().LEARNING_CONTENT_EXPIRE_MINUTES * 60
    await client.set(_lookup_key(user_id, subject, learning_query, grade), content_id, ex=ttl_seconds)


async def get_cached_content_id(user_id: str, subject: str, learning_query: str, grade: str) -> Optional[str]:
    client = get_redis()
    if client is None:
        return None
    return await client.get(_lookup_key(user_id, subject, learning_query, grade))


async def invalidate_cached_learning_content(content_id: str) -> None:
    """Drop the cached copy so the next read repopulates it from MongoDB -
    used after updating the lesson (e.g. marking it complete) so the cache
    doesn't serve stale data."""
    client = get_redis()
    if client is None:
        return
    await client.delete(_key(content_id))
