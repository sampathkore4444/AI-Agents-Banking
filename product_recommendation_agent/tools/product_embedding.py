"""
Product Embedding Tool — ML-based product matching using embeddings.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


# ── In-memory stores ──────────────────────────────────────────────
PRODUCT_EMBEDDINGS: dict[str, dict] = {}
CUSTOMER_EMBEDDINGS: dict[str, dict] = {}


def _generate_embedding(features: dict) -> list[float]:
    """Generate a 128-dimensional embedding from features."""
    np.random.seed(int(hashlib.md5(str(features).encode()).hexdigest()[:8], 16) % 2**31)
    embedding = np.random.randn(128).tolist()
    norm = np.linalg.norm(embedding)
    return [x / norm for x in embedding]


def _compute_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


async def embed_product(
    product_id: str,
    name: str,
    category: str,
    features: dict[str, Any],
) -> dict[str, Any]:
    """Create ML embedding of a product."""
    embedding_features = {
        "name": name,
        "category": category,
        **features,
    }
    embedding = _generate_embedding(embedding_features)

    PRODUCT_EMBEDDINGS[product_id] = {
        "product_id": product_id,
        "name": name,
        "category": category,
        "features": features,
        "embedding": embedding,
    }

    return {
        "product_id": product_id,
        "embedding_dimension": len(embedding),
        "message": f"Product {product_id} embedded.",
    }


async def embed_customer_preferences(
    customer_id: str,
    risk_tolerance: str,
    investment_horizon_years: int,
    income_level: str,
    age_group: str,
    existing_products: list[str],
    preferences: dict[str, Any],
) -> dict[str, Any]:
    """Create ML embedding of customer preferences."""
    features = {
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon_years,
        "income_level": income_level,
        "age_group": age_group,
        "product_count": len(existing_products),
        "preferences": preferences,
    }
    embedding = _generate_embedding(features)

    CUSTOMER_EMBEDDINGS[customer_id] = {
        "customer_id": customer_id,
        "features": features,
        "embedding": embedding,
    }

    return {
        "customer_id": customer_id,
        "embedding_dimension": len(embedding),
        "message": f"Customer {customer_id} preferences embedded.",
    }


async def match_customer_to_products(
    customer_id: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Match customer preferences to products using embeddings."""
    customer_emb = CUSTOMER_EMBEDDINGS.get(customer_id)
    if not customer_emb:
        return {"error": f"Customer {customer_id} not embedded. Call embed_customer_preferences first."}

    matches = []
    for pid, product_emb in PRODUCT_EMBEDDINGS.items():
        similarity = _compute_similarity(customer_emb["embedding"], product_emb["embedding"])
        matches.append({
            "product_id": pid,
            "name": product_emb["name"],
            "category": product_emb["category"],
            "similarity_score": round(similarity, 4),
        })

    matches.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "customer_id": customer_id,
        "matches": matches[:top_k],
        "method": "embedding_cosine_similarity",
    }


async def find_similar_products(
    product_id: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Find similar products using embeddings."""
    source = PRODUCT_EMBEDDINGS.get(product_id)
    if not source:
        return {"error": f"Product {product_id} not embedded."}

    similarities = []
    for pid, emb in PRODUCT_EMBEDDINGS.items():
        if pid == product_id:
            continue
        similarity = _compute_similarity(source["embedding"], emb["embedding"])
        similarities.append({
            "product_id": pid,
            "name": emb["name"],
            "category": emb["category"],
            "similarity_score": round(similarity, 4),
        })

    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "source_product": product_id,
        "similar_products": similarities[:top_k],
    }


async def cluster_customers(
    customer_ids: list[str],
    n_clusters: int = 3,
) -> dict[str, Any]:
    """Cluster customers based on preference embeddings."""
    embeddings = []
    valid_ids = []

    for cid in customer_ids:
        emb = CUSTOMER_EMBEDDINGS.get(cid)
        if emb:
            embeddings.append(emb["embedding"])
            valid_ids.append(cid)

    if len(embeddings) < n_clusters:
        return {"error": f"Not enough embedded customers ({len(embeddings)}) for {n_clusters} clusters"}

    # Simple k-means-like clustering
    np.random.seed(42)
    centroids = np.array([embeddings[i] for i in np.random.choice(len(embeddings), n_clusters, replace=False)])

    for _ in range(10):
        clusters: dict[int, list[str]] = {i: [] for i in range(n_clusters)}
        for idx, emb in enumerate(embeddings):
            emb_arr = np.array(emb)
            distances = [np.linalg.norm(emb_arr - centroids[c]) for c in range(n_clusters)]
            cluster_id = int(np.argmin(distances))
            clusters[cluster_id].append(valid_ids[idx])

        for c in range(n_clusters):
            if clusters[c]:
                cluster_embs = [np.array(embeddings[valid_ids.index(cid)]) for cid in clusters[c]]
                centroids[c] = np.mean(cluster_embs, axis=0)

    return {
        "n_clusters": n_clusters,
        "clusters": [
            {"cluster_id": i, "customer_ids": clusters[i], "size": len(clusters[i])}
            for i in range(n_clusters)
        ],
    }


async def get_embedding_stats() -> dict[str, Any]:
    """Get embedding database statistics."""
    return {
        "total_product_embeddings": len(PRODUCT_EMBEDDINGS),
        "total_customer_embeddings": len(CUSTOMER_EMBEDDINGS),
        "embedding_dimension": 128,
    }
