#!/usr/bin/env python3

import logging
from typing import Optional

from core.config import get_settings
from db.redis.setup import get_redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "quizz:pending:"


def _key(quizz_id: str) -> str:
    return f"{_KEY_PREFIX}{quizz_id}"


async def save_generated_quizz(quizz_id: str, document_json: str) -> None:
    """Cache a freshly generated quizz in Redis with a TTL. While the key
    exists, the quizz is still resumable; once it expires (student never
    came back), its absence is what signals the quizz should be treated as
    abandoned - see Assessment.generate_questions().
    """
    client = get_redis()
    if client is None:
        logger.warning("Redis unavailable - quizz_id=%s won't be resumable from cache", quizz_id)
        return
    await client.set(_key(quizz_id), document_json, ex=get_settings().QUIZ_ABANDON_TIMEOUT_SECONDS)


async def get_cached_quizz(quizz_id: str) -> Optional[str]:
    """
    Fetch the cached quizz document, if it's still within its
    resumable window.
    """
    client = get_redis()
    if client is None:
        return None
    return await client.get(_key(quizz_id))


async def delete_cached_quizz(quizz_id: str) -> None:
    """Remove the cached quizz once it's been completed - no longer needed."""
    client = get_redis()
    if client is None:
        return
    await client.delete(_key(quizz_id))
