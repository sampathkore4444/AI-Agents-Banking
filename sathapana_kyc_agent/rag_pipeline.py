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
from vector_store import VectorStore

logger = logging.getLogger(__name__)

COLLECTIONS = [
    "nbc_regulations",
    "product_policies",
    "document_schemas",
    "risk_typologies",
    "past_kyc_decisions",
]


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
        self._store = VectorStore()
        for name in COLLECTIONS:
            full = f"{settings.vector_collection_prefix}_{name}"
            self._store.get_or_create_collection(full)

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
        query_embedding = self._embed(user_query)
        query_tokens = self._tokenize(user_query)
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
            query_rewrite=user_query,
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