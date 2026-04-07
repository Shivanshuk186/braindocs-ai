from app.services.vector_store import search as vector_search
from app.services.bm25_retriever import search as bm25_search
from app.core.config import TOP_K

def hybrid_search(query_embedding, query):
    v_results = vector_search(query_embedding, TOP_K)
    b_results = bm25_search(query, TOP_K)

    combined = v_results + [
        {"text": r, "source": "bm25", "score": 0.5}
        for r in b_results
    ]

    return combined[:TOP_K]