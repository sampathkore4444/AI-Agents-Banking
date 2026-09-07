"""
Notification Tool — MCP tool stub.

Delegates to the configured `integrations.notify.NotificationProvider`
(Cambodian telco aggregators in production).
"""

from __future__ import annotations

from integrations.notify import TEMPLATES  # noqa: F401  (re-exported for callers)


def send_notification(
    recipient_type: str,
    recipient_id: str,
    channel: str = "sms",
    template_id: str = "kyc_under_review",
    variables: dict | None = None,
) -> dict:
    """Send a templated notification via the configured provider."""
    from integrations import get_providers

    return get_providers().notification.send(recipient_type, recipient_id, channel, template_id, variables)