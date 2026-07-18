import hashlib
from typing import List
from haystack import Document

def deduplicate_chunks(chunk_dicts:List[Document]):
    """
    This function only keep the first occurence of each distinct chunk content
    and drop chunks with no real contents.
    """
    seen_hashes = set()
    unique_chunks = []

    for chunk in chunk_dicts:
        content = (chunk.get("content") or "").strip()
        if not content:
            continue
        content_hash = hashlib.md5(content.encode("utf-8","ignore")).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)
        unique_chunks.append(chunk)
    return unique_chunks

if __name__ == "__main__":
    print("Hello World")
