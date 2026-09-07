"""
Identity Verification Tool — MCP tool stub.

Delegates to the configured `integrations.identity.IdentityProvider`
(Jumio/Onfido/SmileID-style vendor in production).
"""

from __future__ import annotations


def verify_identity(
    customer_id: str,
    document_image_url: str,
    selfie_url: str,
    nationality: str = "KH",
    extracted_data: dict | None = None,
) -> dict:
    """Run liveness check, document authenticity, and face match via the provider."""
    from integrations import get_providers

    return get_providers().identity.verify(customer_id, document_image_url, selfie_url, nationality, extracted_data)