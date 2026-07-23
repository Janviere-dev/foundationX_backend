#!/usr/bin/env python3

from haystack import Document
from haystack.utils import Secret
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from core.config import get_settings

settings = get_settings()

def init_qdrant() -> QdrantDocumentStore:
    return QdrantDocumentStore(
        url=settings.QDRANT_URL,
        index=settings.QDRANT_COLLECTION_NAME,
        embedding_dim=settings.DIMENSION,
        api_key=Secret.from_token(settings.QDRANT_API_KEY),
        timeout=settings.QDRANT_TIMEOUT,
    )

if __name__ == "__main__":
    count = init_qdrant().count_documents()
    print(f"Connected to Qdrant. Collection '{settings.QDRANT_COLLECTION_NAME}' has {count} document(s).")
