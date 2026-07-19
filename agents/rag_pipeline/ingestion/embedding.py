#!/usr/bin/env python3

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List

from haystack import Document
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.utils import ComponentDevice

from agents.rag_pipeline.ingestion.helpers_embedding.handle_duplicate import deduplicate_chunks
from agents.rag_pipeline.ingestion.helpers_embedding.fix_chunks_naming import fix_naming

load_dotenv()

REPO_ROOT = Path(__file__).parent.parent.parent.parent
CACHES_DIR = REPO_ROOT / "caches"
LOGS_DIR = REPO_ROOT / "server_logs"

CHUNKS_PATH = CACHES_DIR / "chunks.json"
LEARNING_CHUNK_PATH = CACHES_DIR / "learning_units.json"
LOG_PATH = LOGS_DIR / "ingestion.log"

CACHES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("MODEL_EMBEDDER", "BAAI/bge-m3")
EMBEDDING_DIMENSION = int(os.getenv("DIMENSION", "1024"))

def clean_learning_materials(learning_chunks:Path) -> List[Document]:
    """
    This function applies cleaning in all the chunks
    """
    with open(learning_chunks, encoding="utf-8") as file:
        chunk_dicts = json.load(file)
    logger.info("Loaded %d raw chunks from %s", len(chunk_dicts), learning_chunks)

    unique_chunks = deduplicate_chunks(chunk_dicts=chunk_dicts)
    logger.info("Deduplicated down to %d unique, non-empty chunks", len(unique_chunks))

    learning_contents = fix_naming(chunk_dicts=unique_chunks)
    logger.info("Fixed naming, %d chunks remain after exclusions", len(learning_contents))
    return learning_contents

def dump_learning_unit(learning_chunk:Path):
    """
    This function deep into file named learning_units.json
    only run if no cached was made
    """
    content = clean_learning_materials(learning_chunks=learning_chunk)
    with open(LEARNING_CHUNK_PATH, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2)
    logger.info("Dumped %d cleaned chunks to %s", len(content), LEARNING_CHUNK_PATH)
    return content

def load_learning_unit(learning_unit:Path) -> List[Document]:
    """
    This function loads learning_units.json
    """
    with open(learning_unit, encoding="utf-8") as file:
        learning_contents = json.load(file)
    logger.info("Loaded %d chunks from %s", len(learning_contents), learning_unit)

    return [Document.from_dict(chunk) for chunk in learning_contents]

def embedding():
    logger.info("=== Starting embedding run ===")
    embedder = SentenceTransformersDocumentEmbedder(
        model=EMBEDDING_MODEL,
        device=ComponentDevice.from_str("cpu"),
        batch_size=64
        )

    logger.info("Loading embedding model %s ...", EMBEDDING_MODEL)
    embedder.warm_up()
    logger.info("Embedding model loaded")

    # load learning_units
    if not LEARNING_CHUNK_PATH.exists():
        logger.info("%s not found, building it from %s", LEARNING_CHUNK_PATH, CHUNKS_PATH)
        dump_learning_unit(learning_chunk=CHUNKS_PATH)
    else:
        logger.info("Found existing %s, reusing it", LEARNING_CHUNK_PATH)

    documents = load_learning_unit(learning_unit=LEARNING_CHUNK_PATH)

    limit = os.getenv("EMBED_LIMIT")
    if limit:
        documents = documents[:int(limit)]
        logger.info("EMBED_LIMIT set: only embedding first %d documents", int(limit))

    logger.info("Embedding %d documents with %s", len(documents), EMBEDDING_MODEL)
    embedded_documents = embedder.run(documents=documents)["documents"]
    logger.info("Embedding complete: %d documents embedded", len(embedded_documents))

    if embedded_documents:
        actual_dim = len(embedded_documents[0].embedding)
        if actual_dim != EMBEDDING_DIMENSION:
            logger.warning(
                "Embedding dimension mismatch: model %s produced %d-dim vectors, "
                "but DIMENSION env var is set to %d. Update DIMENSION in .env to match "
                "before creating/using your Qdrant collection.",
                EMBEDDING_MODEL, actual_dim, EMBEDDING_DIMENSION,
            )
        else:
            logger.info("Embedding dimension confirmed: %d", actual_dim)

    logger.info("=== Embedding run complete ===")
    return embedded_documents

if __name__ == "__main__":
    print(embedding())
