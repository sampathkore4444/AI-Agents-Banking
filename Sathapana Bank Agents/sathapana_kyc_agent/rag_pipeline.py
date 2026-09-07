"""
RAG Pipeline for Sathapana Bank KYC Onboarding Agent.

Hybrid search (BM25 keyword + semantic cosine) with reciprocal rank fusion,
re-ranking, and context assembly over NBC/Cambodia knowledge stored in the
local VectorStore. Mirrors the RAGPipeline API used across the repo.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from sentence_transformers import SentenceTransformer

from config import settings
from vector_store import get_vector_store, VectorStore

logger = logging.getLogger(__name__)

COLLECTIONS = [
    "nbc_regulations",
    "product_policies",
    "document_schemas",
    "risk_typologies",
    "past_kyc_decisions",
]

# Domain term expansion: map short forms to full phrases (and reverse) so a
# compact query like "EDD PEP STR casino" retrieves the right NBC/FATF chunks.
QUERY_EXPANSIONS = {
    "EDD": "enhanced due diligence",
    "CDD": "customer due diligence",
    "KYC": "know your customer",
    "AML": "anti-money laundering",
    "CFT": "countering the financing of terrorism",
    "UBO": "beneficial owner",
    "PEP": "politically exposed person",
    "STR": "suspicious transaction report",
    "SAR": "suspicious activity report",
    "PEPs": "politically exposed persons",
    "FATF": "financial action task force",
}

# Domain synonyms: expansion terms that otherwise reduce recall (the KB uses
# "gambling"/"casino junket" where queries tend to say "gaming", etc.).
DOMAIN_SYNONYMS = {
    "gaming": "gambling casino junket",
    "casino": "gambling junket",
    "gambling": "gaming casino junket",
}


def expand_query(query: str) -> str:
    """Expand domain acronyms and synonyms into full phrases to improve recall."""
    if not query:
        return query
    expanded = query
    for acronym, phrase in QUERY_EXPANSIONS.items():
        if re.search(rf"\b{acronym}\b", query):
            expanded = f"{expanded} {phrase}"
    for term, phrase in DOMAIN_SYNONYMS.items():
        if re.search(rf"\b{term}\b", query):
            expanded = f"{expanded} {phrase}"
    expanded = " ".join(expanded.split())
    return expanded


# ── Data classes ──────────────────────────────────────────────────
@dataclass
class RetrievedChunk:
    """A single chunk retrieved from the vector store."""

    text: str
    metadata: dict
    score: float = 0.0
    collection: str = ""


@dataclass
class RAGResult:
    """Final RAG pipeline output."""

    chunks: list[RetrievedChunk] = field(default_factory=list)
    assembled_context: str = ""
    query_rewrite: str = ""


# ── RAG Pipeline ─────────────────────────────────────────────────
class RAGPipeline:
    """Hybrid-search RAG pipeline backed by the local vector store."""

    def __init__(self) -> None:
        self._embedding_model = SentenceTransformer(settings.embedding_model)
        self._store = get_vector_store()
        for name in COLLECTIONS:
            full = f"{settings.vector_collection_prefix}_{name}"
            self._store.get_or_create_collection(full)
        self._reranker_model = None
        if settings.reranker_enabled:
            self._init_reranker()

    def _init_reranker(self) -> None:
        try:
            from sentence_transformers import CrossEncoder

            self._reranker_model = CrossEncoder(settings.reranker_model)
            logger.info("Reranker active: %s", settings.reranker_model)
        except Exception as exc:  # noqa: BLE001 - graceful fallback to fusion ranking
            self._reranker_model = None
            logger.warning("Reranker unavailable (%s); falling back to fusion ranking", exc)

    @property
    def store(self) -> VectorStore:
        return self._store

    def _embed(self, text: str) -> list[float]:
        return self._embedding_model.encode(text).tolist()

    # ── BM25 (keyword) scoring ────────────────────────────────────
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _bm25_scores(self, collection_name: str, query_tokens: list[str]) -> dict[int, float]:
        col = self._store._collections.get(collection_name)
        if not col:
            return {}
        docs = col["documents"]
        k1, b = 1.5, 0.75
        avgdl = sum(len(self._tokenize(d)) for d in docs) / max(len(docs), 1)
        scores: dict[int, float] = {}
        for idx, doc in enumerate(docs):
            tokens = self._tokenize(doc)
            dl = len(tokens)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            score = 0.0
            for q in query_tokens:
                fq = tf.get(q, 0)
                if fq == 0:
                    continue
                nq = sum(1 for d in docs if q in self._tokenize(d))
                idf = max(0.0, ((len(docs) - nq + 0.5) / (nq + 0.5) + 1.0))
                denom = fq + k1 * (1 - b + b * dl / avgdl)
                score += idf * (fq * (k1 + 1)) / denom
            if score > 0:
                scores[idx] = score
        return scores

    # ── retrieval ─────────────────────────────────────────────────
    def _retrieve(self, collection_name: str, query_embedding: list[float], query_tokens: list[str], n: int = 10) -> list[RetrievedChunk]:
        full = f"{settings.vector_collection_prefix}_{collection_name}"
        semantic = self._store.query(full, query_embedding, n_results=n)
        bm25 = self._bm25_scores(full, query_tokens)

        fused: dict[int, float] = {}
        for rank, hit in enumerate(semantic):
            idx = self._store._collections[full]["ids"].index(hit["id"])
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (60 + rank + 1)
        for idx, score in bm25.items():
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (60 + 1)  # rank 0 weight

        col = self._store._collections[full]
        merged = []
        for idx in sorted(fused, key=fused.get, reverse=True):
            merged.append(
                RetrievedChunk(
                    text=col["documents"][idx],
                    metadata=col["metadatas"][idx],
                    score=fused[idx],
                    collection=collection_name,
                )
            )
        return merged[:n]

    def _rerank(self, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks:
            return chunks
        if self._reranker_model is not None:
            try:
                pairs = [[chunk.text, "-"] for chunk in chunks]
                scores = self._reranker_model.predict(pairs)
                for chunk, score in zip(chunks, scores):
                    chunk.score = round(float(score), 4)
            except Exception as exc:  # noqa: BLE001 - fallback on reranker failure
                logger.warning("Rerank inference failed (%s); using fusion scores", exc)
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:top_k]

    def _assemble_context(self, chunks: list[RetrievedChunk]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("source", chunk.metadata.get("product", chunk.collection))
            parts.append(f"[{i}] ({source}) {chunk.text}")
        return "\n\n".join(parts)

    # ── public API ────────────────────────────────────────────────
    def query(
        self,
        user_query: str,
        n_results_per_collection: int = 10,
        top_k: int = 5,
        collections: list[str] | None = None,
    ) -> RAGResult:
        expanded = expand_query(user_query)
        query_embedding = self._embed(expanded)
        query_tokens = self._tokenize(expanded)
        all_chunks: list[RetrievedChunk] = []
        for col_name in collections or COLLECTIONS:
            full = f"{settings.vector_collection_prefix}_{col_name}"
            if full not in self._store.list_collections():
                continue
            all_chunks.extend(self._retrieve(col_name, query_embedding, query_tokens, n_results_per_collection))

        reranked = self._rerank(all_chunks, top_k=top_k)
        return RAGResult(
            chunks=reranked,
            assembled_context=self._assemble_context(reranked),
            query_rewrite=expanded,
        )

    def query_single(self, collection_name: str, user_query: str, n_results: int = 5) -> list[RetrievedChunk]:
        embedding = self._embed(user_query)
        tokens = self._tokenize(user_query)
        return self._retrieve(collection_name, embedding, tokens, n_results)

    def add_documents(self, collection_name: str, documents: list[str], metadatas: list[dict], ids: list[str]) -> None:
        full = f"{settings.vector_collection_prefix}_{collection_name}"
        embeddings = [self._embed(d) for d in documents]
        self._store.add(full, ids, documents, metadatas, embeddings)
        logger.info("Added %d documents to %s", len(documents), collection_name)

    def collection_count(self, collection_name: str) -> int:
        full = f"{settings.vector_collection_prefix}_{collection_name}"
        return self._store.count(full)