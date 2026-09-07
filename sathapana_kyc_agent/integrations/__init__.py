"""Provider registry: constructs the configured vendor adapters (stub|http)."""

from __future__ import annotations

import logging
from typing import Any

from config import settings
from integrations import bakong as _bakong
from integrations import camfiu as _camfiu
from integrations import identity as _identity
from integrations import notify as _notify
from integrations import ocr as _ocr
from integrations import sanctions as _sanctions

logger = logging.getLogger(__name__)


class Providers:
    """Namespace of concrete provider instances."""

    def __init__(
        self,
        sanctions: _sanctions.SanctionsProvider,
        identity: _identity.IdentityProvider,
        ocr: _ocr.OcrProvider,
        notification: _notify.NotificationProvider,
        bakong: _bakong.BakongProvider,
        camfiu: _camfiu.CamfiuReporter,
    ) -> None:
        self.sanctions = sanctions
        self.identity = identity
        self.ocr = ocr
        self.notification = notification
        self.bakong = bakong
        self.camfiu = camfiu

    def summary(self) -> dict[str, str]:
        return {
            "sanctions": type(self.sanctions).__name__,
            "identity": type(self.identity).__name__,
            "ocr": type(self.ocr).__name__,
            "notification": type(self.notification).__name__,
            "bakong": type(self.bakong).__name__,
            "camfiu": type(self.camfiu).__name__,
        }


_builders: dict[str, Any] = {}


def get_providers() -> Providers:
    """Instantiate providers once per process according to settings."""
    if "providers" in _builders:
        return _builders["providers"]

    def pick(kind: str, stub_cls, http_cls, url: str, token: str):
        provider_name = getattr(settings, f"{kind}_provider", "stub").lower()
        if provider_name == "http":
            if not url:
                raise ValueError(f"{kind.upper()}_API_URL not configured for http provider")
            return http_cls(url, token)
        return stub_cls()

    providers = Providers(
        sanctions=pick("sanctions", _sanctions.StubSanctionsProvider, _sanctions.HttpSanctionsProvider, settings.sanctions_api_url, settings.sanctions_api_token),
        identity=pick("identity", _identity.StubIdentityProvider, _identity.HttpIdentityProvider, settings.identity_api_url, settings.identity_api_token),
        ocr=pick("ocr", _ocr.StubOcrProvider, _ocr.HttpOcrProvider, settings.ocr_api_url, settings.ocr_api_token),
        notification=pick("notification", _notify.StubNotificationProvider, _notify.HttpNotificationProvider, settings.notification_api_url, settings.notification_api_token),
        bakong=pick("bakong", _bakong.StubBakongProvider, _bakong.HttpBakongProvider, settings.nbc_bakong_api_url, ""),
        camfiu=pick("camfiu", _camfiu.StubCamfiuReporter, _camfiu.HttpCamfiuReporter, settings.camfiu_api_url or settings.camfiu_reporting_url + "/str", settings.camfiu_api_token),
    )
    _builders["providers"] = providers
    logger.info("Provider adapters active: %s", providers.summary())
    return providers


def reset_providers() -> None:
    """Clear cached providers (used by tests)."""
    _builders.pop("providers", None)