import logging
import re
from typing import Any

from app.core.config import ENABLE_MULTI_SOURCE_COMPARE, STRICT_SINGLE_SOURCE, TOP_K
from app.core.embeddings import embed
from app.services.bm25_retriever import search as bm25_search
from app.services.llm import generate
from app.services.memory import add
from app.services.vector_store import search as vector_search

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "and",
    "or",
    "what",
    "which",
    "show",
    "tell",
    "about",
    "please",
}

INTENT_TOKENS = {
    "syllabus",
    "unit",
    "curriculum",
    "outline",
    "topics",
    "chapter",
}

MULTI_SOURCE_QUERY_TOKENS = {
    "compare",
    "difference",
    "differences",
    "both",
    "all",
    "across",
    "between",
    "versus",
    "vs",
}


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", (text or "").lower())
        if len(token) >= 2 and token not in STOPWORDS
    }


def _lexical_overlap(query: str, text: str) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    t_tokens = _tokenize(text)
    if not t_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / len(q_tokens)


def _contains_all(tokens: set[str], text: str) -> bool:
    if not tokens:
        return True
    text_tokens = _tokenize(text)
    return tokens.issubset(text_tokens)


def _select_dominant_source(results: list[dict[str, Any]]) -> str | None:
    if not results:
        return None

    source_scores: dict[str, float] = {}
    for item in results:
        source = item.get("source", "unknown")
        source_scores[source] = source_scores.get(source, 0.0) + float(item.get("score", 0.0))

    ranked = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked:
        return None
    if len(ranked) == 1:
        return ranked[0][0]

    top_source, top_score = ranked[0]
    second_score = ranked[1][1]

    if second_score <= 0:
        return top_source

    # Strong source dominance gate to reduce mixed-document contamination.
    if top_score / second_score >= 1.25:
        return top_source

    return None


def _select_best_source(results: list[dict[str, Any]]) -> str | None:
    if not results:
        return None

    source_scores: dict[str, float] = {}
    for item in results:
        source = item.get("source", "unknown")
        source_scores[source] = source_scores.get(source, 0.0) + float(item.get("score", 0.0))

    if not source_scores:
        return None
    return max(source_scores.items(), key=lambda x: x[1])[0]


def _group_by_source(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        source = item.get("source", "unknown")
        grouped.setdefault(source, []).append(item)

    for source in grouped:
        grouped[source].sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)

    return grouped


def _build_single_source_context(results: list[dict[str, Any]], char_budget: int = 2200) -> str:
    blocks: list[str] = []
    used = 0
    for item in results:
        source = item.get("source", "unknown")
        page = item.get("page")
        label = f"{source} page {page}" if page is not None else source
        block = f"[SOURCE: {label}]\n{item.get('text', '')}"
        if used + len(block) > char_budget:
            remaining = max(0, char_budget - used)
            if remaining > 80:
                blocks.append(block[:remaining])
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _build_multi_source_context(results: list[dict[str, Any]], char_budget: int = 2800) -> str:
    grouped = _group_by_source(results)
    ranked_sources = sorted(
        grouped.keys(),
        key=lambda src: sum(float(x.get("score", 0.0)) for x in grouped[src]),
        reverse=True,
    )

    blocks: list[str] = []
    used = 0
    for source in ranked_sources[:3]:
        chunks = grouped[source][:2]
        for item in chunks:
            page = item.get("page")
            label = f"{source} page {page}" if page is not None else source
            block = f"[SOURCE: {label}]\n{item.get('text', '')}"
            if used + len(block) > char_budget:
                remaining = max(0, char_budget - used)
                if remaining > 80:
                    blocks.append(block[:remaining])
                return "\n\n".join(blocks)
            blocks.append(block)
            used += len(block)

    return "\n\n".join(blocks)


def _clean_answer(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return "I don't know"

    lowered = text.lower()
    if "i don't know" in lowered:
        return "I don't know"

    boilerplate_prefixes = (
        "based on the provided context",
        "according to the provided context",
        "the provided context",
    )
    for prefix in boilerplate_prefixes:
        if lowered.startswith(prefix):
            text = re.sub(r"^[^.]*\.\s*", "", text, count=1).strip() or text
            break

    if len(text) > 700:
        text = text[:700].rsplit(" ", 1)[0] + "..."

    return text


def _merge_hybrid_results(
    semantic_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, Any], dict[str, Any]] = {}

    for result in semantic_results:
        key = (result.get("text", ""), result.get("source", "unknown"), result.get("page"))
        merged[key] = {
            "text": result.get("text", ""),
            "source": result.get("source", "unknown"),
            "page": result.get("page"),
            "score": float(result.get("score", 0.0)) * 0.65,
        }

    for result in keyword_results:
        key = (result.get("text", ""), result.get("source", "unknown"), result.get("page"))
        if key in merged:
            merged[key]["score"] += float(result.get("score", 0.0)) * 0.35
        else:
            merged[key] = {
                "text": result.get("text", ""),
                "source": result.get("source", "unknown"),
                "page": result.get("page"),
                "score": float(result.get("score", 0.0)) * 0.35,
            }

    combined = [item for item in merged.values() if item.get("text")]
    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[: max(1, top_k)]


def query_rag(query: str, top_k: int | None = None) -> dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        return {"answer": "I don't know", "sources": []}

    k = top_k if top_k is not None else TOP_K
    k = max(1, k)
    retrieve_k = max(k * 4, 8)

    query_embedding = embed([clean_query])[0]
    semantic_results = vector_search(query_embedding, retrieve_k)
    keyword_results = bm25_search(clean_query, retrieve_k)
    results = _merge_hybrid_results(semantic_results, keyword_results, retrieve_k)

    query_tokens = _tokenize(clean_query)
    must_have = query_tokens.intersection(INTENT_TOKENS)
    multi_source_intent = bool(query_tokens.intersection(MULTI_SOURCE_QUERY_TOKENS))
    is_multi_mode = ENABLE_MULTI_SOURCE_COMPARE and multi_source_intent

    if must_have:
        intent_filtered = [r for r in results if _contains_all(must_have, r.get("text", ""))]
        if intent_filtered:
            results = intent_filtered

    filtered = [r for r in results if _lexical_overlap(clean_query, r.get("text", "")) >= 0.25]
    focused_results = filtered[:k] if filtered else results[:k]

    if STRICT_SINGLE_SOURCE and not is_multi_mode:
        best_source = _select_best_source(focused_results)
        if best_source is not None:
            focused_results = [r for r in focused_results if r.get("source") == best_source][:k]
    else:
        dominant_source = _select_dominant_source(focused_results)
        if dominant_source is not None:
            dominant_only = [r for r in focused_results if r.get("source") == dominant_source]
            if dominant_only:
                focused_results = dominant_only[:k]

    logger.info(
        "RAG retrieval query='%s' semantic=%s bm25=%s merged=%s",
        clean_query,
        len(semantic_results),
        len(keyword_results),
        len(results),
    )

    if not focused_results:
        answer = "I don't know"
        add(clean_query, answer)
        return {"answer": answer, "sources": []}

    if is_multi_mode:
        context = _build_multi_source_context(focused_results)
        prompt = (
            "You are a strict document QA assistant.\n"
            "Use only the supplied context.\n"
            "If the answer is not explicitly in context, respond exactly with: I don't know\n"
            "Do not add external knowledge or assumptions.\n\n"
            "Return a structured source-wise answer in this exact style:\n"
            "- <source-name>: <concise point from that source>\n"
            "Only include sources present in context and relevant to the question.\n"
            "Max 4 bullet points total.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {clean_query}\n"
            "Answer:"
        )
    else:
        context = _build_single_source_context(focused_results)
        primary_source = focused_results[0].get("source", "unknown")
        prompt = (
            "You are a strict document QA assistant.\n"
            "Use only the supplied context.\n"
            "If the answer is not explicitly in context, respond exactly with: I don't know\n"
            "Do not add external knowledge or assumptions.\n\n"
            "Single-source grounding is required.\n"
            f"Primary source: {primary_source}\n"
            "Answer format:\n"
            "1) Direct answer in 1-3 sentences.\n"
            "2) A final line: Source: <source-name>\n"
            "Keep answer below 120 words and avoid unrelated details.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {clean_query}\n"
            "Answer:"
        )

    answer = _clean_answer(generate(prompt))
    add(clean_query, answer)

    sources = [
        {
            "source": item.get("source", "unknown"),
            "page": item.get("page"),
            "score": round(float(item.get("score", 0.0)), 4),
        }
        for item in focused_results
    ]

    return {"answer": answer, "sources": sources}