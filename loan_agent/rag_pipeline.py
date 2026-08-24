"""
RAG Pipeline for Loan Application Processing Agent.

Provides hybrid search over loan regulations, product policies,
eligibility criteria, and underwriting guidelines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)

# ── Collection names ──────────────────────────────────────────────
COLLECTIONS = [
    "loan_regulations",
    "product_policies",
    "eligibility_criteria",
    "underwriting_guidelines",
    "past_loan_decisions",
    "fair_lending_guidelines",
    "credit_scoring_models",
]


@dataclass
class RetrievedChunk:
    """A single chunk retrieved from the vector DB."""
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


class RAGPipeline:
    """Hybrid-search RAG pipeline backed by ChromaDB."""

    def __init__(self) -> None:
        self._embedding_model = SentenceTransformer(settings.embedding_model)
        self._chroma = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            )
        )
        self._collections: dict[str, chromadb.Collection] = {}
        for name in COLLECTIONS:
            self._collections[name] = self._chroma.get_or_create_collection(
                name=f"{settings.chroma_collection_prefix}_{name}",
                metadata={"hnsw:space": "cosine"},
            )

    def _embed(self, text: str) -> list[float]:
        return self._embedding_model.encode(text).tolist()

    def _query_collection(
        self, collection_name: str, query_embedding: list[float], n_results: int = 10,
    ) -> list[RetrievedChunk]:
        col = self._collections[collection_name]
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, col.count() or 1),
        )
        chunks: list[RetrievedChunk] = []
        if results and results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [{}] * len(results["documents"][0]),
                results["distances"][0] if results["distances"] else [0.0] * len(results["documents"][0]),
            ):
                score = 1.0 - dist
                chunks.append(RetrievedChunk(text=doc, metadata=meta if meta else {}, score=score, collection=collection_name))
        return chunks

    def _rerank(self, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:top_k]

    def _assemble_context(self, chunks: list[RetrievedChunk]) -> str:
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("source", chunk.metadata.get("product", chunk.collection))
            parts.append(f"[{i}] ({source}) {chunk.text}")
        return "\n\n".join(parts)

    def query(self, user_query: str, n_results_per_collection: int = 5, top_k: int = 5, collections: list[str] | None = None) -> RAGResult:
        query_embedding = self._embed(user_query)
        all_chunks: list[RetrievedChunk] = []
        target_collections = collections or COLLECTIONS
        for col_name in target_collections:
            if col_name in self._collections:
                all_chunks.extend(self._query_collection(col_name, query_embedding, n_results_per_collection))
        reranked = self._rerank(all_chunks, top_k=top_k)
        context = self._assemble_context(reranked)
        return RAGResult(chunks=reranked, assembled_context=context, query_rewrite=user_query)

    def query_single(self, collection_name: str, user_query: str, n_results: int = 5) -> list[RetrievedChunk]:
        embedding = self._embed(user_query)
        return self._query_collection(collection_name, embedding, n_results)

    def add_documents(self, collection_name: str, documents: list[str], metadatas: list[dict], ids: list[str]) -> None:
        embeddings = [self._embed(doc) for doc in documents]
        col = self._collections[collection_name]
        col.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)
        logger.info("Added %d documents to %s", len(documents), collection_name)

    def collection_count(self, collection_name: str) -> int:
        return self._collections[collection_name].count()
