"""
Conversation Analysis Tool — Analyze lead conversations for intent and qualification signals.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── Intent keywords and signals ───────────────────────────────────
INTENT_SIGNALS = {
    "high_intent": ["apply now", "ready to apply", "want to open", "sign me up", "let's do it", "when can i start", "how do i apply"],
    "medium_intent": ["tell me more", "what are the rates", "how does it work", "what do i need", "what are the fees", "can i qualify"],
    "low_intent": ["just looking", "exploring options", "thinking about it", "maybe later", "not sure yet", "just browsing"],
    "competitor_mentions": ["i have at chase", "my current bank", "bank of america", "wells fargo", "i'm with ally", "marcus"],
    "pain_points": ["too many fees", "bad rates", "poor service", "long wait times", "hidden charges", "complicated process"],
    "urgency_signals": ["need it soon", "by end of month", "closing on a house", "starting a business", "urgent", "asap"],
}


async def analyze_conversation(
    lead_id: str,
    messages: list[dict],
    channel: str,
) -> dict[str, Any]:
    """Analyze a conversation for intent and qualification signals."""
    # Combine all message text
    full_text = " ".join(m.get("text", "") for m in messages).lower()

    # Detect intent signals
    detected_signals = {
        "high_intent": [],
        "medium_intent": [],
        "low_intent": [],
        "competitor_mentions": [],
        "pain_points": [],
        "urgency_signals": [],
    }

    for signal_type, keywords in INTENT_SIGNALS.items():
        for keyword in keywords:
            if keyword in full_text:
                detected_signals[signal_type].append(keyword)

    # Calculate intent score
    high_count = len(detected_signals["high_intent"])
    medium_count = len(detected_signals["medium_intent"])
    low_count = len(detected_signals["low_intent"])

    if high_count > 0:
        intent_level = "high"
        intent_score = min(80 + high_count * 10, 100)
    elif medium_count > high_count:
        intent_level = "medium"
        intent_score = 50 + medium_count * 5
    elif low_count > 0:
        intent_level = "low"
        intent_score = 20 + low_count * 5
    else:
        intent_level = "neutral"
        intent_score = 40

    # Extract key questions
    questions = [m.get("text", "") for m in messages if m.get("text", "").endswith("?")]

    # Extract product mentions
    product_keywords = ["savings", "checking", "credit card", "mortgage", "loan", "investment", "ira", "cd"]
    products_mentioned = [p for p in product_keywords if p in full_text]

    # Sentiment (simple keyword-based)
    positive_words = ["great", "excellent", "love", "perfect", "yes", "interested", "sounds good"]
    negative_words = ["no", "not interested", "bad", "expensive", "too much", "no thanks"]
    pos_count = sum(1 for w in positive_words if w in full_text)
    neg_count = sum(1 for w in negative_words if w in full_text)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Qualification signals
    qualification_signals = []
    if any(s in full_text for s in ["income", "salary", "make"]):
        qualification_signals.append("budget_discussed")
    if any(s in full_text for s in ["credit score", "my score"]):
        qualification_signals.append("credit_discussed")
    if any(s in full_text for s in ["looking for", "need", "want"]):
        qualification_signals.append("need_expressed")
    if any(s in full_text for s in ["when", "how soon", "timeline"]):
        qualification_signals.append("timeline_discussed")

    return {
        "lead_id": lead_id,
        "channel": channel,
        "message_count": len(messages),
        "intent": {
            "level": intent_level,
            "score": intent_score,
            "signals": detected_signals,
        },
        "questions_asked": questions,
        "products_mentioned": products_mentioned,
        "sentiment": sentiment,
        "qualification_signals": qualification_signals,
        "recommendations": _generate_recommendations(intent_level, sentiment, qualification_signals),
    }


def _generate_recommendations(intent_level: str, sentiment: str, qualification_signals: list[str]) -> list[str]:
    """Generate action recommendations based on analysis."""
    recs = []

    if intent_level == "high":
        recs.append("Route to senior advisor immediately")
        recs.append("Prepare application materials")
    elif intent_level == "medium":
        recs.append("Send follow-up email with product details")
        recs.append("Schedule consultation within 48 hours")
    elif intent_level == "low":
        recs.append("Add to nurture campaign")
        recs.append("Send educational content")

    if sentiment == "negative":
        recs.append("Address concerns before proceeding")
        recs.append("Consider alternative products")

    if len(qualification_signals) < 2:
        recs.append("Conduct qualification call to gather more information")

    if "budget_discussed" not in qualification_signals:
        recs.append("Ask about financial goals and budget")

    return recs


async def get_conversation_history(lead_id: str) -> dict[str, Any]:
    """Get conversation history for a lead."""
    # Simulated conversation history
    return {
        "lead_id": lead_id,
        "total_interactions": 3,
        "conversations": [
            {"date": "2026-08-18", "channel": "web", "summary": "Initial inquiry about savings account"},
            {"date": "2026-08-19", "channel": "email", "summary": "Sent product comparison, asked about rates"},
            {"date": "2026-08-20", "channel": "phone", "summary": "Discussed qualification requirements"},
        ],
    }


async def get_intent_keywords() -> dict[str, Any]:
    """Get all intent signal keywords."""
    return INTENT_SIGNALS
