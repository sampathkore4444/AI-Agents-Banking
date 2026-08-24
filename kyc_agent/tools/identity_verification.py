"""
Identity Verification Tool — MCP tool stub.

In production this would call Jumio / Onfido / Smile ID.
Here we return simulated results for development.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def verify_identity(
    customer_id: str,
    document_image_url: str,
    selfie_url: str,
    extracted_data: dict | None = None,
) -> dict:
    """
    Perform identity verification: liveness check, document authenticity, face match.

    Returns a verification result dict.
    """
    logger.info("Verifying identity for customer %s", customer_id)

    # ── In production: call Jumio/Onfido API ──
    # response = await httpx.AsyncClient().post(
    #     f"{settings.jumio_api_url}/v2/idnets/{customer_id}",
    #     headers={"Authorization": f"Bearer {settings.jumio_api_key}"},
    #     json={...},
    # )

    # ── Stub: deterministic result based on input ──
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

    result = {
        "verification_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "liveness_check": liveness,
        "document_authenticity": authenticity,
        "face_match": face_match,
        "overall_result": overall,
        "checked_at": datetime.utcnow().isoformat(),
        "extracted_data_used": extracted_data or {},
    }

    logger.info("Identity verification result: %s", overall)
    return result
