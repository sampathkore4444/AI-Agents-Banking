"""CAMFIU STR reporting: payload schema validation + provider adapters.

`build_str_record(...)` validates the Suspicious Transaction Report payload
against a required-field schema before any external submission, so malformed
STRs are caught at the edge (config: CAMFIU_API_URL/TOKEN or stub).
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from integrations.base import post_json

STR_VERSION = "1.0"
STR_FILING_TYPE = "STR"


class StrEntity(BaseModel):
    le_name: str
    le_id: str = ""
    reg_authority: str = "NBC"
    contact_desk: str = ""


class StrCustomer(BaseModel):
    customer_ref: str
    full_name: str
    id_number: str | None = None
    id_type: str | None = None
    nationality: str = "KH"
    customer_type: str = "individual"


class StrAmount(BaseModel):
    currency: str
    amount: float = Field(gt=0)


class STRRecord(BaseModel):
    """CAMFIU Suspicious Transaction Report (validated before filing)."""

    report_version: str = STR_VERSION
    filing_type: str = STR_FILING_TYPE
    reporting_entity: StrEntity
    customer: StrCustomer
    account_refs: list[str] = Field(default_factory=list)
    detection_tool: str = "sathapana_kyc_agent"
    grounds_flags: list[str] = Field(default_factory=list)
    narrative: str = Field(min_length=20)
    amounts: list[StrAmount] = Field(default_factory=list)
    event_date: str
    filing_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    filed_by: str = ""

    @property
    def str_reference(self) -> str:
        return f"STR-{uuid.uuid4().hex[:10].upper()}"


REQUIRED_STR_FIELDS = ["report_version", "filing_type", "reporting_entity", "customer", "narrative", "event_date", "filing_date"]


def build_str_record(
    case: dict,
    customer: dict | None = None,
    agent_id: str = "kyc-agent",
    narrative_max: int = 500,
) -> tuple[STRRecord | None, dict]:
    """Build + validate an STRRecord from a compliance case.

    Returns (record, info) on success, or (None, {"validation_error": ...})
    listing missing/invalid required fields, so the caller can reject before
    anything is filed.
    """
    errors: list[str] = []
    if not customer or not customer.get("full_name"):
        errors.append("customer.full_name")
    if not case.get("summary"):
        errors.append("case.summary")
    if not case.get("risk_level"):
        errors.append("case.risk_level")

    if errors:
        return None, {"validation_error": {"missing_fields": errors, "case_id": case.get("case_id")}}

    flags = case.get("flags") or []
    if isinstance(flags, str):
        try:
            flags = json.loads(flags)
        except json.JSONDecodeError:
            flags = [flags]

    try:
        record = STRRecord(
            reporting_entity=StrEntity(le_name=case.get("bank_name", "") or "Sathapana Bank PLC", le_id=case.get("bank_lei", "")),
            customer=StrCustomer(
                customer_ref=str(customer.get("customer_id") or ""),
                full_name=str(customer.get("full_name") or ""),
                id_number=customer.get("id_number"),
                id_type=customer.get("id_type"),
                nationality=customer.get("nationality", "KH"),
                customer_type=str(customer.get("customer_type", "individual")),
            ),
            account_refs=case.get("account_refs") or [],
            grounds_flags=flags,
            narrative=case.get("summary", "")[:narrative_max],
            amounts=case.get("amounts") or [],
            event_date=case.get("created_at") or datetime.now(timezone.utc).isoformat(),
            filed_by=agent_id,
        )
    except ValidationError as exc:
        missing = [f"{'.'.join(str(p) for p in e['loc'])}" for e in exc.errors()]
        return None, {"validation_error": {"missing_fields": missing, "case_id": case.get("case_id")}}

    return record, {"validated": True, "required_fields": REQUIRED_STR_FIELDS}


class CamfiuReporter(ABC):
    @abstractmethod
    def file(self, record: STRRecord) -> dict:
        """Transmit a validated STR to CAMFIU and return the reference."""


class StubCamfiuReporter(CamfiuReporter):
    def file(self, record: STRRecord) -> dict:
        return {
            "str_reference": record.str_reference,
            "authority": "Cambodia Financial Intelligence Unit (CAMFIU)",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "record_version": record.report_version,
            "summary": record.narrative,
            "provider": "stub",
        }


class HttpCamfiuReporter(CamfiuReporter):
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def file(self, record: STRRecord) -> dict:
        payload = record.model_dump(mode="json")
        result = post_json(self.url, self.token, payload)
        result.setdefault("str_reference", record.str_reference)
        result.setdefault("provider", "http")
        return result