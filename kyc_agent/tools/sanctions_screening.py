"""
Sanctions & PEP Screening Tool — MCP tool stub.

In production this would call OFAC, EU, UN sanctions APIs and PEP databases.
Here we return simulated results for development.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def screen_sanctions(
    full_name: str,
    date_of_birth: str,
    nationality: str,
    aliases: list[str] | None = None,
) -> dict:
    """
    Screen a customer against global sanctions lists and PEP databases.

    Returns screening results for OFAC, EU, UN, and PEP status.
    """
    logger.info("Screening sanctions for %s (DOB: %s, Nationality: %s)", full_name, date_of_birth, nationality)

    # ── In production: call OFAC / EU / UN APIs ──
    # response = await httpx.AsyncClient().post(
    #     f"{settings.ofac_api_url}/v1/screen",
    #     json={"name": full_name, "dob": date_of_birth, "nationality": nationality},
    # )

    # ── Stub: hash-based deterministic results ──
    name_hash = hashlib.md5(full_name.lower().encode()).hexdigest()
    hash_val = int(name_hash[:8], 16) % 100

    ofac = "clear" if hash_val > 10 else "potential_match"
    eu_sanc = "clear" if hash_val > 10 else "potential_match"
    un_sanc = "clear" if hash_val > 10 else "potential_match"
    pep = "not_pep" if hash_val > 20 else "domestic_pep"
    adverse_media = hash_val < 5

    # Determine risk level
    has_hits = ofac != "clear" or eu_sanc != "clear" or un_sanc != "clear"
    if has_hits:
        risk = "high"
    elif pep != "not_pep" or adverse_media:
        risk = "medium"
    else:
        risk = "low"

    result = {
        "screening_id": str(uuid.uuid4()),
        "customer_name": full_name,
        "date_of_birth": date_of_birth,
        "nationality": nationality,
        "ofac_result": ofac,
        "eu_sanctions_result": eu_sanc,
        "un_sanctions_result": un_sanc,
        "pep_status": pep,
        "adverse_media": adverse_media,
        "risk_level": risk,
        "screened_at": datetime.utcnow().isoformat(),
        "aliases_checked": aliases or [],
    }

    logger.info("Sanctions screening result: risk=%s, ofac=%s", risk, ofac)
    return result
