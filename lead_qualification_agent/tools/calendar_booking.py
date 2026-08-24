"""
Calendar Booking Tool — Schedule meetings and consultations with leads.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


# ── In-memory calendar store ──────────────────────────────────────
CALENDAR_DB: list[dict] = []
ADVISOR_DB: dict[str, dict] = {
    "advisor_001": {"name": "Alice Johnson", "title": "Senior Financial Advisor", "specialties": ["mortgage", "investment"], "availability": "high"},
    "advisor_002": {"name": "Bob Williams", "title": "Personal Banking Advisor", "specialties": ["checking", "savings", "credit_card"], "availability": "medium"},
    "advisor_003": {"name": "Carol Davis", "title": "Wealth Management Advisor", "specialties": ["investment", "retirement"], "availability": "high"},
}


async def book_appointment(
    lead_id: str,
    advisor_id: str | None,
    product_interest: str,
    preferred_date: str,
    preferred_time: str,
    meeting_type: str = "consultation",
    channel: str = "phone",
) -> dict[str, Any]:
    """Book an appointment with an advisor."""
    # Auto-assign advisor if not specified
    if not advisor_id:
        for aid, advisor in ADVISOR_DB.items():
            if product_interest in advisor.get("specialties", []):
                if advisor["availability"] in ("high", "medium"):
                    advisor_id = aid
                    break
        if not advisor_id:
            advisor_id = "advisor_001"  # Default

    advisor = ADVISOR_DB.get(advisor_id, {"name": "Unknown", "title": "Advisor"})

    appointment = {
        "appointment_id": f"APT-{int(datetime.utcnow().timestamp())}",
        "lead_id": lead_id,
        "advisor_id": advisor_id,
        "advisor_name": advisor["name"],
        "product_interest": product_interest,
        "date": preferred_date,
        "time": preferred_time,
        "meeting_type": meeting_type,
        "channel": channel,
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }
    CALENDAR_DB.append(appointment)

    return {
        "appointment_id": appointment["appointment_id"],
        "advisor": advisor["name"],
        "date": preferred_date,
        "time": preferred_time,
        "channel": channel,
        "message": f"Appointment booked with {advisor['name']} on {preferred_date} at {preferred_time}.",
    }


async def get_available_slots(
    advisor_id: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    """Get available appointment slots."""
    # Simulated available slots
    slots = [
        {"date": "2026-08-25", "time": "10:00", "advisor": "Alice Johnson"},
        {"date": "2026-08-25", "time": "14:00", "advisor": "Bob Williams"},
        {"date": "2026-08-26", "time": "09:00", "advisor": "Carol Davis"},
        {"date": "2026-08-26", "time": "11:00", "advisor": "Alice Johnson"},
        {"date": "2026-08-26", "time": "15:00", "advisor": "Bob Williams"},
        {"date": "2026-08-27", "time": "10:00", "advisor": "Carol Davis"},
        {"date": "2026-08-27", "time": "13:00", "advisor": "Alice Johnson"},
    ]

    if advisor_id:
        advisor_name = ADVISOR_DB.get(advisor_id, {}).get("name", "")
        slots = [s for s in slots if s["advisor"] == advisor_name]
    if date:
        slots = [s for s in slots if s["date"] == date]

    return {"available_slots": slots, "total": len(slots)}


async def cancel_appointment(appointment_id: str, reason: str) -> dict[str, Any]:
    """Cancel an appointment."""
    for apt in CALENDAR_DB:
        if apt["appointment_id"] == appointment_id:
            apt["status"] = "cancelled"
            apt["cancel_reason"] = reason
            return {"appointment_id": appointment_id, "status": "cancelled", "message": "Appointment cancelled."}
    return {"error": f"Appointment {appointment_id} not found"}


async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str,
) -> dict[str, Any]:
    """Reschedule an appointment."""
    for apt in CALENDAR_DB:
        if apt["appointment_id"] == appointment_id:
            apt["date"] = new_date
            apt["time"] = new_time
            apt["status"] = "rescheduled"
            return {"appointment_id": appointment_id, "new_date": new_date, "new_time": new_time, "message": "Appointment rescheduled."}
    return {"error": f"Appointment {appointment_id} not found"}


async def get_appointments(
    advisor_id: str | None = None,
    date: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Get appointments filtered by criteria."""
    results = CALENDAR_DB[:]
    if advisor_id:
        results = [a for a in results if a["advisor_id"] == advisor_id]
    if date:
        results = [a for a in results if a["date"] == date]
    if status:
        results = [a for a in results if a["status"] == status]

    return {"total": len(results), "appointments": results}


async def get_advisors() -> dict[str, Any]:
    """Get available advisors."""
    return {"advisors": list(ADVISOR_DB.values())}
