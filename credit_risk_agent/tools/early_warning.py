"""
Early Warning System Tool — MCP tool stub.

Detects deteriorating credit quality through:
- Financial metric trends
- Payment behavior changes
- Market signal deterioration
- Rating downgrade predictions
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def run_early_warning_scan(portfolio_id: str = "main") -> dict:
    """Scan entire portfolio for early warning signals."""
    logger.info("Running early warning scan for portfolio %s", portfolio_id)
    p_hash = hashlib.md5(portfolio_id.encode()).hexdigest()
    hv = int(p_hash[:8], 16)

    num_borrowers = 200 + hv % 300
    alerts_generated = []
    for i in range(5):
        b_id = f"BORR-{(hv + i * 100) % 10000:04d}"
        severity = ["low", "medium", "high", "critical"][hv % 4]
        signals = []
        if hv % 3 == 0:
            signals.append("declining_revenue")
        if hv % 4 == 0:
            signals.append("increasing_leverage")
        if hv % 5 == 0:
            signals.append("payment_delinquency")
        if hv % 7 == 0:
            signals.append("negative_news")
        alerts_generated.append({
            "borrower_id": b_id,
            "severity": severity,
            "signals": signals if signals else ["marginal_deterioration"],
            "risk_score_change": round(-5 - (hv % 15), 1),
        })

    return {
        "scan_id": str(uuid.uuid4()),
        "portfolio_id": portfolio_id,
        "borrowers_scanned": num_borrowers,
        "alerts_generated": len(alerts_generated),
        "alerts": alerts_generated,
        "critical_count": sum(1 for a in alerts_generated if a["severity"] == "critical"),
        "high_count": sum(1 for a in alerts_generated if a["severity"] == "high"),
        "medium_count": sum(1 for a in alerts_generated if a["severity"] == "medium"),
        "low_count": sum(1 for a in alerts_generated if a["severity"] == "low"),
        "scanned_at": datetime.utcnow().isoformat(),
    }


async def check_borrower_signals(borrower_id: str) -> dict:
    """Check early warning signals for a specific borrower."""
    logger.info("Checking signals for borrower %s", borrower_id)
    b_hash = hashlib.md5(borrower_id.encode()).hexdigest()
    hv = int(b_hash[:8], 16)

    signals = []
    if hv % 3 == 0:
        signals.append({"signal": "revenue_decline", "severity": "medium", "detail": "Revenue declined 15% YoY"})
    if hv % 4 == 0:
        signals.append({"signal": "leverage_increase", "severity": "high", "detail": "Debt/EBITDA increased to 4.5x"})
    if hv % 5 == 0:
        signals.append({"signal": "payment_delinquency", "severity": "high", "detail": "30+ days past due on term loan"})
    if hv % 7 == 0:
        signals.append({"signal": "negative_news", "severity": "medium", "detail": "Negative press coverage detected"})
    if hv % 11 == 0:
        signals.append({"signal": "covenant_breach", "severity": "critical", "detail": "Interest coverage covenant breached"})
    if not signals:
        signals.append({"signal": "no_significant_deterioration", "severity": "low", "detail": "All metrics stable"})

    overall_risk = "critical" if any(s["severity"] == "critical" for s in signals) else "high" if any(s["severity"] == "high" for s in signals) else "medium" if len(signals) > 2 else "low"

    return {
        "borrower_id": borrower_id,
        "signals": signals,
        "num_signals": len(signals),
        "overall_risk_level": overall_risk,
        "recommended_action": (
            "Immediate review required" if overall_risk == "critical"
            else "Enhanced monitoring" if overall_risk == "high"
            else "Standard monitoring" if overall_risk == "medium"
            else "No action required"
        ),
        "checked_at": datetime.utcnow().isoformat(),
    }


async def get_watchlist() -> dict:
    """Get current watchlist of deteriorating borrowers."""
    logger.info("Fetching watchlist")
    # Stub: simulate watchlist
    watchlist = [
        {"borrower_id": "BORR-0042", "status": "on_watch", "days_on_watch": 45, "risk_level": "high", "trigger": "leverage_increase"},
        {"borrower_id": "BORR-0187", "status": "on_watch", "days_on_watch": 120, "risk_level": "critical", "trigger": "covenant_breach"},
        {"borrower_id": "BORR-0293", "status": "under_review", "days_on_watch": 30, "risk_level": "medium", "trigger": "payment_delinquency"},
    ]
    return {
        "watchlist": watchlist,
        "count": len(watchlist),
        "critical": sum(1 for w in watchlist if w["risk_level"] == "critical"),
        "high": sum(1 for w in watchlist if w["risk_level"] == "high"),
        "updated_at": datetime.utcnow().isoformat(),
    }
