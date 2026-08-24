"""
Payment Embedding Tool — MCP tool stub.

Creates ML embeddings of payment references, invoice details, and counterparty
information for semantic matching of unmatched payments.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory embedding store
_embeddings: dict[str, dict] = {}


async def embed_invoice(
    invoice_id: str,
    vendor_name: str,
    amount: float,
    invoice_date: str,
    description: str,
    po_number: str | None = None,
    line_items: list[dict] | None = None,
) -> dict:
    """Create embedding of an invoice for semantic matching."""
    logger.info("Embedding invoice: %s", invoice_id)

    feature_string = f"{invoice_id}{vendor_name}{amount}{invoice_date}{description}{po_number or ''}"
    hash_val = int(hashlib.md5(feature_string.encode()).hexdigest()[:16], 16)

    embedding = []
    for i in range(128):
        seed = (hash_val + i * 7919) % 10000
        embedding.append(round((seed / 10000.0) * 2 - 1, 4))

    result = {
        "invoice_id": invoice_id,
        "vendor_name": vendor_name,
        "amount": amount,
        "embedding_dimensions": 128,
        "embedding_preview": embedding[:10],
        "embedding_full": embedding,
        "embedded_at": datetime.utcnow().isoformat(),
    }

    _embeddings[invoice_id] = result
    return result


async def embed_payment(
    payment_id: str,
    payer_name: str,
    amount: float,
    payment_date: str,
    reference: str,
    payment_method: str,
    bank_reference: str | None = None,
) -> dict:
    """Create embedding of a payment for semantic matching."""
    logger.info("Embedding payment: %s", payment_id)

    feature_string = f"{payment_id}{payer_name}{amount}{payment_date}{reference}{payment_method}"
    hash_val = int(hashlib.md5(feature_string.encode()).hexdigest()[:16], 16)

    embedding = []
    for i in range(128):
        seed = (hash_val + i * 7919) % 10000
        embedding.append(round((seed / 10000.0) * 2 - 1, 4))

    result = {
        "payment_id": payment_id,
        "payer_name": payer_name,
        "amount": amount,
        "embedding_dimensions": 128,
        "embedding_preview": embedding[:10],
        "embedding_full": embedding,
        "embedded_at": datetime.utcnow().isoformat(),
    }

    _embeddings[payment_id] = result
    return result


async def find_similar_invoices(
    payment_id: str,
    top_k: int = 5,
) -> dict:
    """Find invoices similar to a payment using embedding similarity."""
    payment_emb = _embeddings.get(payment_id)
    if not payment_emb:
        return {"error": f"Payment embedding {payment_id} not found"}

    payment_vector = payment_emb["embedding_full"]

    similarities = []
    for eid, emb_data in _embeddings.items():
        if eid == payment_id:
            continue
        if not emb_data.get("invoice_id"):
            continue

        sim = _cosine_similarity(payment_vector, emb_data["embedding_full"])
        similarities.append({
            "invoice_id": eid,
            "vendor_name": emb_data.get("vendor_name", ""),
            "amount": emb_data.get("amount", 0),
            "similarity_score": round(sim, 4),
        })

    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "payment_id": payment_id,
        "payment_amount": payment_emb.get("amount", 0),
        "similar_invoices": similarities[:top_k],
        "match_confident": similarities[0]["similarity_score"] > 0.9 if similarities else False,
    }


async def embed_counterparty(counterparty_id: str, name: str, aliases: list[str] | None = None) -> dict:
    """Create embedding of a counterparty name with aliases."""
    all_names = [name] + (aliases or [])
    feature_string = "|".join(all_names)
    hash_val = int(hashlib.md5(feature_string.encode()).hexdigest()[:16], 16)

    embedding = []
    for i in range(128):
        seed = (hash_val + i * 7919) % 10000
        embedding.append(round((seed / 10000.0) * 2 - 1, 4))

    result = {
        "counterparty_id": counterparty_id,
        "name": name,
        "aliases": aliases or [],
        "embedding_dimensions": 128,
        "embedding_preview": embedding[:10],
        "embedded_at": datetime.utcnow().isoformat(),
    }

    _embeddings[counterparty_id] = result
    return result


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
