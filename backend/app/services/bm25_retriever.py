import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

bm25: BM25Okapi | None = None
docs: list[dict[str, Any]] = []


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower())


def build(documents: list[dict[str, Any]]) -> None:
    global bm25, docs

    docs = []
    bm25 = None

    if not documents:
        logger.warning("BM25 build skipped: no documents")
        return

    tokenized: list[list[str]] = []
    for item in documents:
        text = (item.get("text") or "").strip()
        tokens = _tokenize(text)
        if not tokens:
            continue
        docs.append(
            {
                "text": text,
                "source": item.get("source", "unknown"),
                "page": item.get("page"),
            }
        )
        tokenized.append(tokens)

    if not tokenized:
        logger.warning("BM25 build skipped: corpus has no tokens")
        return

    bm25 = BM25Okapi(tokenized)
    logger.info("BM25 built with %s documents", len(docs))


def search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    if bm25 is None or not docs:
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)

    results: list[dict[str, Any]] = []
    for idx, score in indexed[: max(1, top_k)]:
        item = docs[idx]
        results.append(
            {
                "text": item["text"],
                "source": item.get("source", "unknown"),
                "page": item.get("page"),
                "score": float(score),
            }
        )

    if not results:
        return []

    max_score = max(result["score"] for result in results) or 1.0
    for result in results:
        result["score"] = result["score"] / max_score

    return results