"""Ingestion pipeline: load PDFs -> chunk -> batch-index into Azure AI Search -> verify.

Usage:
    python ingest.py             # index all PDFs in data/
    python ingest.py --reset     # delete the index first (full rebuild)
    python ingest.py --dry-run   # load + chunk only, no Azure calls
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import time
from collections import Counter

from config import ConfigError, get_config
from src.data_loader import TravelDataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ingest")
logging.getLogger("azure").setLevel(logging.WARNING)  # the SDK logs every HTTP header at INFO

BATCH_SIZE = 50
MAX_RETRIES = 3


def _doc_key(chunk) -> str:
    """Azure AI Search keys allow only letters, digits, '_', '-' and '='; the hash is deterministic,
    so re-running the ingestion updates existing chunks instead of duplicating them."""
    return hashlib.sha1(chunk.metadata["chunk_id"].encode("utf-8")).hexdigest()


def index_in_batches(vector_store, chunks, batch_size: int = BATCH_SIZE) -> int:
    """Add chunks in batches (with retry/back-off) so rate limits do not abort the run."""
    indexed = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                vector_store.add_texts([c.page_content for c in batch], [c.metadata for c in batch],
                                       keys=[_doc_key(c) for c in batch])
                indexed += len(batch)
                logger.info("Indexed %d/%d chunks", indexed, len(chunks))
                break
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise
                wait = 2 ** attempt
                logger.warning("Batch failed (%s); retry %d/%d in %ds", exc, attempt, MAX_RETRIES, wait)
                time.sleep(wait)
    return indexed


def verify_index(search_client, expected: int, wait_seconds: int = 10) -> int:
    """Poll the document count (Azure AI Search is eventually consistent) and compare it to ``expected``."""
    count = 0
    for _ in range(max(1, wait_seconds // 2)):
        count = search_client.get_document_count()
        if count >= expected:
            break
        time.sleep(2)
    if count < expected:
        raise RuntimeError(f"Index verification failed: expected >= {expected} documents, found {count}")
    logger.info("Index verification OK: %d documents in index (expected %d)", count, expected)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest WanderNest PDFs into Azure AI Search")
    parser.add_argument("--reset", action="store_true", help="delete and recreate the index")
    parser.add_argument("--dry-run", action="store_true", help="load and chunk only")
    args = parser.parse_args()

    try:
        cfg = get_config(validate=True, require_search=True) if not args.dry_run else get_config(validate=False)
    except ConfigError as exc:
        raise SystemExit(str(exc))

    loader = TravelDataLoader(cfg.data_dir, cfg.chunk_size, cfg.chunk_overlap)
    documents = loader.load_documents()
    chunks = loader.chunk_documents(documents)
    by_cat = Counter(c.metadata["category"] for c in chunks)
    logger.info("Loaded %d pages -> %d chunks | by category: %s", len(documents), len(chunks), dict(by_cat))
    if args.dry_run:
        return

    from src.vector_store import get_index_client, get_search_client, get_vector_store

    if args.reset:
        try:
            get_index_client(cfg).delete_index(cfg.search_index_name)
            logger.info("Deleted index '%s'", cfg.search_index_name)
        except Exception as exc:
            logger.info("Nothing to delete (%s)", exc)

    store = get_vector_store(cfg)
    indexed = index_in_batches(store, chunks)
    verify_index(get_search_client(cfg), expected=indexed)
    logger.info("Ingestion complete: %d chunks indexed into '%s'", indexed, cfg.search_index_name)


if __name__ == "__main__":
    main()
