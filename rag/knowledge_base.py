"""
Knowledge Base — builds and caches the FAISS vector store from seed documents.
Provides category-filtered retrievers used by each domain agent.

Uses OpenAI embeddings; run with --rebuild-rag after changing the embedding model.
"""
from __future__ import annotations

import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

import config
from data.seed_documents import DOCUMENTS


# ── Document conversion ───────────────────────────────────────────────────────

def _to_langchain_docs(raw_docs: list[dict]) -> List[Document]:
    return [
        Document(
            page_content=d["content"],
            metadata={
                "id": d["id"],
                "title": d["title"],
                "category": d["category"],
                "tags": ",".join(d.get("tags", [])),
            },
        )
        for d in raw_docs
    ]


# ── Singleton vector store ────────────────────────────────────────────────────

_store: FAISS | None = None


def _get_store() -> FAISS:
    global _store
    if _store is not None:
        return _store

    embeddings = config.get_embeddings()
    store_path = config.VECTOR_STORE_PATH

    if os.path.exists(os.path.join(store_path, "index.faiss")):
        _store = FAISS.load_local(
            store_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    else:
        docs = _to_langchain_docs(DOCUMENTS)
        _store = FAISS.from_documents(docs, embeddings)
        _store.save_local(store_path)

    return _store


def rebuild_store() -> FAISS:
    """Force rebuild even if store already exists on disk."""
    global _store
    embeddings = config.get_embeddings()
    docs = _to_langchain_docs(DOCUMENTS)
    _store = FAISS.from_documents(docs, embeddings)
    _store.save_local(config.VECTOR_STORE_PATH)
    return _store


# ── Public retriever factory ──────────────────────────────────────────────────

CATEGORY_FILTER = {
    "quality":     ["kba", "standard", "incident"],
    "throughput":  ["kba", "standard", "maintenance", "incident"],
    "supplier":    ["supplier", "standard", "incident"],
    "maintenance": ["maintenance", "kba", "incident"],
    "safety":      ["standard", "incident", "kba"],
    "rca":         ["kba", "standard", "incident", "maintenance", "supplier"],
    "all":         ["kba", "standard", "incident", "maintenance", "supplier"],
}


def get_retriever(domain: str = "all", k: int = None) -> VectorStoreRetriever:
    """
    Return a retriever filtered to the relevant document categories for a domain.
    domain: one of the keys in CATEGORY_FILTER or "all"
    """
    k = k or config.RAG_TOP_K
    store = _get_store()
    allowed_cats = CATEGORY_FILTER.get(domain, CATEGORY_FILTER["all"])

    def _filter(metadata: dict) -> bool:
        return metadata.get("category") in allowed_cats

    return store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            "filter": _filter,
        },
    )


def retrieve_docs(query: str, domain: str = "all", k: int = None) -> List[Document]:
    """Convenience wrapper — returns a flat list of Document objects."""
    retriever = get_retriever(domain=domain, k=k or config.RAG_TOP_K)
    return retriever.invoke(query)


def retrieve_as_text(query: str, domain: str = "all", k: int = None) -> str:
    """Return retrieved documents as a single formatted string."""
    docs = retrieve_docs(query, domain=domain, k=k)
    if not docs:
        return "No relevant documents found."
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        parts.append(
            f"[{i}] {meta.get('title', 'Unknown')} (ID: {meta.get('id', '?')}, "
            f"Category: {meta.get('category', '?')})\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)
