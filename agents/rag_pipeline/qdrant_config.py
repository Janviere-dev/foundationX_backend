#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from haystack import Document
from haystack.utils import Secret
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

load_dotenv()

def init_qdrant() -> QdrantDocumentStore:
    return QdrantDocumentStore(
        url=os.getenv("QDRANT_URL"),
        index=os.getenv("QDRANT_COLLECTION_NAME"),
        embedding_dim=int(os.getenv("DIMENSION")),
        api_key=Secret.from_env_var("QDRANT_API_KEY"),
        timeout=int(os.getenv("QDRANT_TIMEOUT", "60")),
    )

if __name__ == "__main__":
    count = init_qdrant().count_documents()
    print(f"Connected to Qdrant. Collection '{os.getenv('QDRANT_COLLECTION_NAME')}' has {count} document(s).")
