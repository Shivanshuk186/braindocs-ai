import logging
from pathlib import Path
from typing import Any

from app.core.embeddings import embed
from app.services.bm25_retriever import build as build_bm25
from app.services.chunker import chunk_text
from app.services import vector_store
from app.utils.file_loader import load_file

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_ROOM_DIR = BASE_DIR / "data_room"


def _ingest_records(source: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    all_chunks: list[str] = []
    all_metas: list[dict[str, Any]] = []

    for record in records:
        text = (record.get("text") or "").strip()
        if not text:
            continue

        page = record.get("page")
        chunks = [c.strip() for c in chunk_text(text) if c and c.strip()]
        logger.info("Chunking %s page=%s -> %s chunks", source, page, len(chunks))

        for chunk in chunks:
            all_chunks.append(chunk)
            all_metas.append({"source": source, "page": page})

    if not all_chunks:
        logger.warning("No valid chunks generated for %s", source)
        return {"status": "skipped", "source": source, "chunks": 0}

    embeddings = embed(all_chunks)
    if not embeddings:
        logger.warning("Embedding model returned no vectors for %s", source)
        return {"status": "skipped", "source": source, "chunks": 0}

    vector_store.clear_source(source)
    vector_store.add_embeddings(embeddings=embeddings, docs=all_chunks, metas=all_metas)

    corpus = vector_store.get_corpus()
    build_bm25(corpus)
    vector_store.save()

    logger.info("Ingested %s with %s chunks", source, len(all_chunks))
    return {
        "status": "indexed",
        "source": source,
        "chunks": len(all_chunks),
        "documents": vector_store.document_count(),
    }


def ingest_file(filename: str, content: bytes) -> dict[str, Any]:
    vector_store.load()

    records = load_file(filename=filename, content=content)
    if not records:
        logger.warning("Empty parse result for %s", filename)
        return {"status": "skipped", "source": filename, "chunks": 0}

    return _ingest_records(source=filename, records=records)


def ingest_data_room() -> dict[str, Any]:
    vector_store.load()

    if not DATA_ROOM_DIR.exists():
        logger.info("data_room not found at %s", DATA_ROOM_DIR)
        build_bm25(vector_store.get_corpus())
        return {"status": "ok", "files": 0, "indexed": 0, "failed": 0}

    indexed = 0
    failed = 0
    files = 0

    for path in sorted(DATA_ROOM_DIR.iterdir()):
        if not path.is_file():
            continue

        files += 1
        try:
            result = ingest_file(filename=path.name, content=path.read_bytes())
            if result.get("status") == "indexed":
                indexed += 1
        except Exception as exc:
            failed += 1
            logger.exception("Failed ingesting %s: %s", path.name, exc)

    logger.info("Data room ingestion complete files=%s indexed=%s failed=%s", files, indexed, failed)
    return {"status": "ok", "files": files, "indexed": indexed, "failed": failed}