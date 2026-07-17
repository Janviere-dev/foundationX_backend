#!/usr/bin/env python3

import json
import asyncio
from pathlib import Path
from haystack import Document
from typing import List
from haystack.components.preprocessors import DocumentSplitter as HaystackDocumentSplitter

from .helpers.helper_remove_cover import MAX_PAGE_CHARS, is_front_matter

class DocumentSplitter:
    def __init__(self):
        self.page_splitter = HaystackDocumentSplitter(
            split_by="page",
            split_length=1,
            split_overlap=0
        )
        self.sentence_splitter = HaystackDocumentSplitter(
            split_by="sentence",
            split_length=10,
            split_overlap=2
        )

    def run_splitter(self, documents:list[Document]):
        """Split by page; any page longer than MAX_PAGE_CHARS is further split by sentence."""
        pages = self.page_splitter.run(documents=documents)["documents"]

        chunks = []
        for page in pages:
            if is_front_matter(page):
                continue

            if len(page.content) <= MAX_PAGE_CHARS:
                chunks.append(page)
                continue

            sentence_chunks = self.sentence_splitter.run(documents=[page])["documents"]
            for sentence_chunk in sentence_chunks:
                # the sentence splitter re-counts page breaks within just this one page's
                # text (there are none), so it would otherwise reset page_number to 1
                sentence_chunk.meta["page_number"] = page.meta["page_number"]
            chunks.extend(sentence_chunks)

        return chunks
    
    def split_chunks(self, documents:list[Document])->list[Document]:
        """this function split document"""
        return self.run_splitter(documents=documents)

def load_cached_document(file_name: str) -> Document:
    """Load a single cached document from document_split.json by file_name, for fast chunking iteration."""
    cache_path = Path(__file__).parent.parent.parent.parent / "document_split.json"
    with open(cache_path, encoding="utf-8") as cache_file:
        cached_documents = json.load(cache_file)
    document_dict = next(
        doc for doc in cached_documents
        if doc.get("file_name") == file_name and doc.get("content")
    )
    #print(document_dict)
    return Document.from_dict(document_dict)


if __name__ == "__main__":
    document_splitter = DocumentSplitter()
    sample_document = load_cached_document("Physics S3 SB.pdf")
    #print(sample_document)
    #print("______________________________________________________________________________________")
    with open(Path(__file__).parent.parent.parent.parent / "document_split.json", encoding='utf-8') as file:
        cached_documents = json.load(file)
    document_list = [Document.from_dict(doc) for doc in cached_documents if doc.get("content")]

    chunks = document_splitter.split_chunks(documents=document_list)
    print(f"Total chunks: {len(chunks)}")
    for chunk in chunks[:5]:
        print(chunk.meta.get("file_name"), chunk.meta.get("page_number"), "->", chunk.content[:1000])
        print("\n")
    """
    chunks = document_splitter.run_splitter(documents=[sample_document])
    for chunk_index, chunk in enumerate(chunks[:10]):
        print("=" * 100)
        print(f"Chunk {chunk_index}")
        '''
        print(f"file_name={chunk.meta.get('file_name')} "
              f"page_number={chunk.meta.get('page_number')} "
              f"subject={chunk.meta.get('subject')}")
        '''
        print(chunk.content[:2000])
        print(chunk.meta)
"""
