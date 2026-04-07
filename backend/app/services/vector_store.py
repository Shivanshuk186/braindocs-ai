import logging
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
VECTOR_DIR = BASE_DIR / "vector_db"
VECTOR_PATH = VECTOR_DIR / "index.faiss"
META_PATH = VECTOR_DIR / "meta.pkl"

index: faiss.IndexFlatL2 | None = None
documents: list[str] = []
metadata: list[dict[str, Any]] = []
vectors: np.ndarray | None = None
loaded = False


def _rebuild_index_from_vectors() -> None:
    global index
    if vectors is None or len(vectors) == 0:
        index = None
        return

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors.astype("float32"))


def init_index(dim: int) -> None:
    global index
    index = faiss.IndexFlatL2(dim)


def document_count() -> int:
    return len(documents)


def get_corpus() -> list[dict[str, Any]]:
    return [
        {
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page": meta.get("page"),
        }
        for doc, meta in zip(documents, metadata)
    ]


def add_embeddings(embeddings: list[list[float]], docs: list[str], metas: list[dict[str, Any]]) -> None:
    global vectors, documents, metadata

    if not embeddings or not docs or not metas:
        logger.warning("Skipping add_embeddings due to empty input")
        return

    arr = np.array(embeddings, dtype="float32")
    if arr.ndim != 2 or arr.shape[0] != len(docs) or len(docs) != len(metas):
        raise ValueError("Embeddings/docs/metadata length mismatch")

    if vectors is None or len(vectors) == 0:
        vectors = arr
    else:
        if vectors.shape[1] != arr.shape[1]:
            raise ValueError("Embedding dimension mismatch in vector store")
        vectors = np.vstack([vectors, arr])

    documents.extend(docs)
    metadata.extend(metas)
    _rebuild_index_from_vectors()


def clear_source(source: str) -> int:
    global documents, metadata, vectors
    if not source or not metadata:
        return 0

    keep_indices = [i for i, meta in enumerate(metadata) if meta.get("source") != source]
    removed = len(metadata) - len(keep_indices)
    if removed == 0:
        return 0

    documents = [documents[i] for i in keep_indices]
    metadata = [metadata[i] for i in keep_indices]

    if vectors is not None and len(vectors) > 0:
        vectors = vectors[keep_indices] if keep_indices else None

    _rebuild_index_from_vectors()
    logger.info("Removed %s existing chunks for source=%s", removed, source)
    return removed


def search(query_embedding: list[float], top_k: int) -> list[dict[str, Any]]:
    if index is None or not documents:
        return []

    top_k = min(max(1, top_k), len(documents))
    q = np.array([query_embedding], dtype="float32")
    distances, indices = index.search(q, top_k)

    results: list[dict[str, Any]] = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx < 0 or idx >= len(documents):
            continue
        sim_score = 1.0 / (1.0 + float(distance))
        meta = metadata[idx] if idx < len(metadata) else {}
        results.append(
            {
                "text": documents[idx],
                "source": meta.get("source", "unknown"),
                "page": meta.get("page"),
                "score": sim_score,
            }
        )

    return results


def save() -> None:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    if index is not None:
        faiss.write_index(index, str(VECTOR_PATH))

    with META_PATH.open("wb") as f:
        pickle.dump(
            {
                "documents": documents,
                "metadata": metadata,
                "vectors": vectors,
            },
            f,
        )


def load() -> None:
    global index, documents, metadata, vectors, loaded
    if loaded:
        return

    documents = []
    metadata = []
    vectors = None
    index = None

    if META_PATH.exists():
        with META_PATH.open("rb") as f:
            data = pickle.load(f)
            documents = data.get("documents", []) or []
            metadata = data.get("metadata", []) or []
            vectors = data.get("vectors")

    if VECTOR_PATH.exists():
        index = faiss.read_index(str(VECTOR_PATH))

    if (index is None) and (vectors is not None) and len(vectors) > 0:
        _rebuild_index_from_vectors()

    loaded = True
    logger.info("Vector store loaded. documents=%s", len(documents))