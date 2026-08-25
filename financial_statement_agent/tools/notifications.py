"""
Notification Tools — Alerts and reports for financial analysis.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
_notification_log: list[dict[str, Any]] = []


async def send_analysis_complete(
    company_id: str,
    company_name: str,
    analysis_type: str,
    summary: dict[str, Any],
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send notification when analysis is complete."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    if channels is None:
        channels = ["email"]

    message = f"Financial analysis complete for {company_name} ({company_id}). Type: {analysis_type}"

    _log_notification(notif_id, company_id, "analysis_complete", message, channels, summary)
    return {"success": True, "notification_id": notif_id, "type": "analysis_complete"}


async def send_deterioration_alert(
    company_id: str,
    company_name: str,
    risk_level: str,
    warnings: list[dict[str, Any]],
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send alert when financial deterioration is detected."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    if channels is None:
        channels = ["email", "push"]

    warning_summary = "; ".join(w["detail"] for w in warnings[:3])
    message = f"Deterioration Alert ({risk_level.upper()}) for {company_name}: {warning_summary}"

    _log_notification(notif_id, company_id, "deterioration_alert", message, channels, {"risk_level": risk_level, "warnings": warnings})
    return {"success": True, "notification_id": notif_id, "type": "deterioration_alert", "risk_level": risk_level}


async def send_benchmark_alert(
    company_id: str,
    company_name: str,
    metric: str,
    company_value: float,
    benchmark_median: float,
    comparison: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send alert when metric deviates significantly from benchmark."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    if channels is None:
        channels = ["email"]

    message = f"Benchmark Alert: {company_name} {metric} = {company_value} (industry median: {benchmark_median}) — {comparison}"

    _log_notification(notif_id, company_id, "benchmark_alert", message, channels, {"metric": metric, "value": company_value, "benchmark": benchmark_median})
    return {"success": True, "notification_id": notif_id, "type": "benchmark_alert"}


async def send_compliance_issue(
    company_id: str,
    company_name: str,
    issues: list[dict[str, Any]],
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send alert for compliance issues found."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    if channels is None:
        channels = ["email", "push"]

    critical = sum(1 for i in issues if i.get("severity") == "critical")
    message = f"Compliance Issue: {company_name} has {len(issues)} issues ({critical} critical)"

    _log_notification(notif_id, company_id, "compliance_issue", message, channels, {"issues": issues})
    return {"success": True, "notification_id": notif_id, "type": "compliance_issue", "critical_count": critical}


async def generate_executive_summary(
    company_id: str,
    company_name: str,
    ratio_analysis: dict[str, Any],
    benchmark_comparison: dict[str, Any] | None = None,
    trend_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an executive summary of the financial analysis."""
    health = ratio_analysis.get("overall_health", {})
    health_rating = health.get("health_rating", "unknown")

    sections = []

    # Health overview
    sections.append(f"## Executive Summary: {company_name}\nOverall Health: {health_rating.upper()} (Score: {health.get('score', 0)})")

    # Key strengths
    strengths = []
    weaknesses = []

    liq = ratio_analysis.get("liquidity", {})
    if liq.get("current_ratio", 0) >= 1.5:
        strengths.append(f"Strong liquidity (Current Ratio: {liq['current_ratio']})")
    elif liq.get("current_ratio", 0) < 1.0:
        weaknesses.append(f"Weak liquidity (Current Ratio: {liq['current_ratio']})")

    lev = ratio_analysis.get("leverage", {})
    if lev.get("debt_to_equity", 0) < 1.0:
        strengths.append(f"Conservative leverage (D/E: {lev['debt_to_equity']})")
    elif lev.get("debt_to_equity", 0) > 2.0:
        weaknesses.append(f"High leverage (D/E: {lev['debt_to_equity']})")

    prof = ratio_analysis.get("profitability", {})
    if prof.get("net_margin_pct", 0) > 10:
        strengths.append(f"Strong profitability (Net Margin: {prof['net_margin_pct']}%)")
    elif prof.get("net_margin_pct", 0) < 0:
        weaknesses.append(f"Unprofitable (Net Margin: {prof['net_margin_pct']}%)")

    z = ratio_analysis.get("altman_zscore", {})
    if z.get("z_score", 0) > 3.0:
        strengths.append(f"Low bankruptcy risk (Z-Score: {z['z_score']})")
    elif z.get("z_score", 0) < 1.8:
        weaknesses.append(f"Elevated bankruptcy risk (Z-Score: {z['z_score']})")

    if strengths:
        sections.append("\n### Strengths\n" + "\n".join(f"- {s}" for s in strengths))
    if weaknesses:
        sections.append("\n### Concerns\n" + "\n".join(f"- {w}" for w in weaknesses))

    # Risk signals
    signals = health.get("risk_signals", [])
    if signals:
        sections.append(f"\n### Risk Signals: {', '.join(signals)}")

    summary_text = "\n".join(sections)
    return {
        "company_id": company_id,
        "company_name": company_name,
        "health_rating": health_rating,
        "summary": summary_text,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risk_signals": signals,
    }


async def get_notification_log(
    company_id: str | None = None,
    notification_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get notification log."""
    results = _notification_log.copy()
    if company_id:
        results = [n for n in results if n["company_id"] == company_id]
    if notification_type:
        results = [n for n in results if n["type"] == notification_type]
    results = sorted(results, key=lambda n: n["sent_at"], reverse=True)[:limit]
    return {"count": len(results), "notifications": results}


def _log_notification(
    notif_id: str, company_id: str, notif_type: str,
    message: str, channels: list[str], data: dict | None = None,
) -> None:
    _notification_log.append({
        "notification_id": notif_id,
        "company_id": company_id,
        "type": notif_type,
        "message": message,
        "channels": channels,
        "data": data,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    })
