#!/usr/bin/env python3

import asyncio
from haystack import Document
from typing import List
from agents.rag_pipeline.qdrant_config import init_qdrant
from agents.rag_pipeline.qdrant_config import QdrantDocumentStore
from haystack.document_stores.types import DuplicatePolicy

from agents.rag_pipeline.ingestion.embedding import embedding


class StoreEmbedding:
    def __init__(self, qdrant_store:QdrantDocumentStore):
        self.__qdrant_store = qdrant_store
    
    def meta_data(self) -> set[str]:
        """
        prepare for storage
        """
        return {
            "file_name",
            "subject",
            "grade",
            "page_number",
            "sparse_embedding",
            "date_added"
            }

    async def store_embedding(self) -> int:
        """
        This function store vector embedding
        """
        embedding_docs = embedding()
        document_to_save = [
            Document.from_dict({
                "id":document.id,
                "content":document.content,
                "embedding":document.embedding,
                "score":document.score,
                "meta": {
                    key:value for key, value in document.meta.items() if key in self.meta_data()
                    }
                }) for document in embedding_docs]
        return await self.__qdrant_store.write_documents_async(
            documents=document_to_save,
            policy=DuplicatePolicy.OVERWRITE
            )

async def main():
    document_store = StoreEmbedding(qdrant_store=init_qdrant())
    return await document_store.store_embedding()

print(asyncio.run(main()))
