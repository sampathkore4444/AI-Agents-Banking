"""
Lightweight persistent vector store (numpy + JSON).

Provides the same collection-based API used across the repo (add, query,
count) with cosine-similarity retrieval and on-disk persistence. This keeps
the reference implementation runnable with zero extra dependencies; swap for
ChromaDB/pgvector in production by implementing the same four methods.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Persistent cosine-similarity vector store backed by .npz/.json files."""

    def __init__(self, root_dir: str | None = None) -> None:
        self.root = os.path.abspath(root_dir or os.path.join(settings.data_dir, "vector_store"))
        os.makedirs(self.root, exist_ok=True)
        self._collections: dict[str, dict] = {}
        self._load_all()

    # ── persistence ───────────────────────────────────────────────
    def _collection_paths(self, name: str) -> tuple[str, str]:
        return (
            os.path.join(self.root, f"{name}.npz"),
            os.path.join(self.root, f"{name}.json"),
        )

    def _load_all(self) -> None:
        for filename in os.listdir(self.root):
            if filename.endswith(".npz"):
                name = filename[:-4]
                self._load_collection(name)

    def _load_collection(self, name: str) -> None:
        npz_path, json_path = self._collection_paths(name)
        if not (os.path.exists(npz_path) and os.path.exists(json_path)):
            return
        with open(json_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        arrays = np.load(npz_path)
        self._collections[name] = {
            "ids": meta["ids"],
            "documents": meta["documents"],
            "metadatas": meta["metadatas"],
            "embeddings": arrays["embeddings"],
        }

    def _persist(self, name: str) -> None:
        col = self._collections.get(name)
        if not col:
            return
        npz_path, json_path = self._collection_paths(name)
        np.savez(npz_path, embeddings=np.asarray(col["embeddings"], dtype=np.float32))
        meta = {
            "ids": col["ids"],
            "documents": col["documents"],
            "metadatas": col["metadatas"],
        }
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False)

    # ── collection lifecycle ──────────────────────────────────────
    def get_or_create_collection(self, name: str) -> str:
        """Create a collection if missing and return its name."""
        if name not in self._collections:
            self._collections[name] = {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "embeddings": np.zeros((0, 0), dtype=np.float32),
            }
            self._persist(name)
        return name

    def list_collections(self) -> list[str]:
        return list(self._collections.keys())

    def count(self, name: str) -> int:
        return len(self._collections.get(name, {}).get("ids", []))

    # ── writes ────────────────────────────────────────────────────
    def add(self, name: str, ids: list[str], documents: list[str], metadatas: list[dict], embeddings: list[list[float]]) -> None:
        col = self._collections[name]
        dim = len(embeddings[0]) if embeddings else 0
        new_emb = np.asarray(embeddings, dtype=np.float32).reshape(-1, dim)
        if col["embeddings"].size == 0:
            col["embeddings"] = new_emb
        else:
            col["embeddings"] = np.vstack([col["embeddings"], new_emb])
        col["ids"].extend(ids)
        col["documents"].extend(documents)
        col["metadatas"].extend(metadatas)
        self._persist(name)

    def reset(self, name: str) -> None:
        self._collections.pop(name, None)
        for path in self._collection_paths(name):
            if os.path.exists(path):
                os.remove(path)

    # ── retrieval ─────────────────────────────────────────────────
    def query(self, name: str, embedding: list[float], n_results: int = 10) -> list[dict]:
        """Return top-n matches as [{id, document, metadata, score}] (1.0 = best)."""
        col = self._collections.get(name)
        if not col or col["embeddings"].size == 0:
            return []

        query_vec = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        norms = np.linalg.norm(col["embeddings"], axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        similarity = np.clip(
            (query_vec @ col["embeddings"].T) / (np.linalg.norm(query_vec) * norms),
            0.0, 1.0,
        )[0]

        k = min(n_results, len(col["ids"]))
        top_idx = np.argsort(similarity)[::-1][:k]
        results = []
        for i in top_idx:
            results.append(
                {
                    "id": col["ids"][int(i)],
                    "document": col["documents"][int(i)],
                    "metadata": col["metadatas"][int(i)],
                    "score": float(similarity[int(i)]),
                }
            )
        return results


# ── helper for callers that generate ids ─────────────────────────
def gen_id(prefix: str = "doc") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ── backend factory ───────────────────────────────────────────────
def get_vector_store() -> VectorStore:
    """Instantiate the configured vector store backend.

    numpy (default, zero dependencies) | chromadb (needs `pip install
    chromadb`). A missing chromadb package raises an informative error so a
    misconfigured deployment fails fast.
    """
    backend = settings.vector_backend.lower()
    if backend == "numpy":
        return VectorStore()
    if backend in ("chroma", "chromadb"):
        try:
            import chromadb  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "vector_backend=chromadb is configured but the 'chromadb' package is not installed. "
                "Install it ('python -m pip install chromadb') or set VECTOR_BACKEND=numpy."
            ) from exc
        return _ChromaVectorStore()

    raise ValueError(f"Unknown vector_backend: {settings.vector_backend} (use 'numpy' or 'chromadb')")


class _ChromaVectorStore:
    """Thin ChromaDB adapter exposing the same collection API as VectorStore."""

    def __init__(self) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=os.path.join(settings.data_dir, "chroma"))
        self._collections: dict[str, Any] = {}

    def get_or_create_collection(self, name: str) -> str:
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(name=name)
        return name

    def list_collections(self) -> list[str]:
        return [c.name for c in self._client.list_collections()]

    def count(self, name: str) -> int:
        if name not in self._collections:
            return 0
        return self._collections[name].count()

    def add(self, name: str, ids: list[str], documents: list[str], metadatas: list[dict], embeddings: list[list[float]]) -> None:
        self.get_or_create_collection(name)
        self._collections[name].add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def reset(self, name: str) -> None:
        if name in self._collections:
            self._client.delete_collection(name=name)
            del self._collections[name]

    def query(self, name: str, embedding: list[float], n_results: int = 10) -> list[dict]:
        if name not in self._collections or self.count(name) == 0:
            return []
        hits = self._collections[name].query(query_embeddings=[embedding], n_results=n_results, include=["documents", "metadatas", "distances"])
        out = []
        for i, doc in enumerate(hits["documents"][0]):
            out.append(
                {
                    "id": hits["ids"][0][i],
                    "document": doc,
                    "metadata": hits["metadatas"][0][i],
                    "score": float(1.0 - hits["distances"][0][i]),
                }
            )
        return out