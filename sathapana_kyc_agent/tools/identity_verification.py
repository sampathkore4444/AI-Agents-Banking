"""
Identity Verification Tool — MCP tool stub.

In production this calls Jumio / Onfido / SmileID (or a local Khmer-capable
verification partner). Returns simulated results for development.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone


def verify_identity(
    customer_id: str,
    document_image_url: str,
    selfie_url: str,
    nationality: str = "KH",
    extracted_data: dict | None = None,
) -> dict:
    """Perform liveness check, document authenticity, and face match."""
    doc_hash = hashlib.md5(document_image_url.encode()).hexdigest()
    is_valid_hash = int(doc_hash[:8], 16) % 100

    liveness = "pass" if is_valid_hash > 5 else "fail"
    authenticity = "authentic" if is_valid_hash > 5 else "suspected_fraud"
    face_match = round(min(max(is_valid_hash / 100.0, 0.4), 0.99), 2)

    if liveness == "pass" and authenticity == "authentic" and face_match > 0.7:
        overall = "verified"
    elif liveness == "fail" or authenticity == "suspected_fraud":
        overall = "rejected"
    else:
        overall = "manual_review"

    return {
        "verification_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "nationality": nationality,
        "liveness_check": liveness,
        "document_authenticity": authenticity,
        "face_match": face_match,
        "overall_result": overall,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "extracted_data_used": extracted_data or {},
    }