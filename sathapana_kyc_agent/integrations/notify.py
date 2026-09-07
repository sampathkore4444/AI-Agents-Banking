"""Notification provider adapters (SMS via Smart/Metfone/Cellcard, email, push)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from integrations.base import post_json

TEMPLATES = {
    "kyc_welcome": "Welcome to Sathapana Bank, {customer_name}!",
    "kyc_documents_requested": "Dear {customer_name}, we need more documents for your KYC: {missing}.",
    "kyc_under_review": "Your application is under compliance review. We will update you within 24 hours.",
    "kyc_approved": "Congratulations {customer_name}! Your {product} account {account_id} is ready.",
    "kyc_rejected": "We are unable to proceed with your application. Contact your branch or CAMFIU.",
    "kyc_additional_info": "Please provide additional information to complete verification: {items}.",
}


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient_type: str, recipient_id: str, channel: str, template_id: str, variables: dict | None) -> dict:
        """Dispatch a templated message."""


class StubNotificationProvider(NotificationProvider):
    """Logs/queues the message locally (no carrier)."""

    def send(self, recipient_type: str, recipient_id: str, channel: str, template_id: str, variables: dict | None = None) -> dict:
        message = TEMPLATES.get(template_id, "Sathapana Bank notification.")
        try:
            message = message.format(**(variables or {}))
        except KeyError:
            pass
        return {
            "notification_id": "ntf_stub_" + uuid.uuid4().hex[:10],
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
            "channel": channel,
            "template_id": template_id,
            "message": message,
            "status": "queued",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "provider": "stub",
        }


class HttpNotificationProvider(NotificationProvider):
    """Calls an SMS/email gateway (config: NOTIFICATION_API_URL/TOKEN)."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def send(self, recipient_type: str, recipient_id: str, channel: str, template_id: str, variables: dict | None = None) -> dict:
        payload: dict[str, Any] = {
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
            "channel": channel,
            "template_id": template_id,
            "variables": variables or {},
        }
        result = post_json(self.url, self.token, payload)
        result.setdefault("provider", "http")
        return result