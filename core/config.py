#!/usr/bin/env python3

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # Cloudflare R2
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_JURISDICTION: str
    BUCKET_URL: str

    # Parallel operation
    MAX_WORKERS: int
    BATCH_SIZE: int

    # Embedding
    MODEL_EMBEDDER: str
    EMBED_LIMIT: Optional[int] = None
    DIMENSION: int
    STORE_SLICE_SIZE: int
    EMBED_BATCH_SIZE: int
    EMBED_DEVICE: str

    # Qdrant Cloud
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str
    QDRANT_TIMEOUT: int
    TOP_K: int = 5

    # MongoDB Cloud
    MONGODB_URI: str
    MONGO_DB_NAME: str
    MONGO_COLLECTION_NAME: str
    MONGODB_USER: str
    MONGODB_PASSWORD: str

    # OCR / chunking run (agents/rag_pipeline/ingestion/run_ocr_and_chunk.py)
    OCR_WORKERS: int
    OCR_LIMIT: Optional[int] = None
    OCR_FILES: Optional[str] = None

    # Qdrant storage run tuning (agents/rag_pipeline/ingestion/store.py)
    STORE_MAX_RETRIES: int
    STORE_RETRY_DELAY: int

    # Gemini API key
    GOOGLE_API_KEY:str
    LLM_MODEL:str
    LLM_MODEL_FALLBACK:str
    GOOGLE_API_KEY_FALLBACK:str
    LLM_ENABLED:bool = False
    ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS:bool
    LLM_MAX_RETRIES:int
    LLM_RETRY_DELAY:int

    # Tavily web search tool
    TAVILY_API_KEY:str

    @field_validator("EMBED_LIMIT", "OCR_LIMIT", "OCR_FILES", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
