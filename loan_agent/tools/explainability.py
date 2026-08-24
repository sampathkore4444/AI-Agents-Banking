"""
Explainability Tool — MCP tool stub.

Generates detailed, human-readable explanations for credit decisions.
Required by ECOA and fair lending regulations for adverse action notices.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def explain_decision(
    application_id: str,
    decision: str,
    credit_score: int,
    dti_ratio: float,
    ltv_ratio: float,
    risk_factors: list[str],
    income_verified: bool,
    employment_type: str,
) -> dict:
    """
    Generate a detailed explanation for a credit decision.

    Produces:
    - Plain-English explanation of the decision
    - Key factors that influenced the decision
    - Specific adverse action reasons (if declined)
    - Steps to improve (if declined)
    - Regulatory compliance (ECOA adverse action notice requirements)
    """
    logger.info("Generating explanation for application %s: decision=%s", application_id, decision)

    # Build factor explanations
    factor_details = []

    # Credit score factor
    if credit_score >= 750:
        factor_details.append({
            "factor": "Credit Score",
            "value": credit_score,
            "impact": "positive",
            "explanation": f"Your credit score of {credit_score} is excellent, indicating strong credit history.",
        })
    elif credit_score >= 700:
        factor_details.append({
            "factor": "Credit Score",
            "value": credit_score,
            "impact": "positive",
            "explanation": f"Your credit score of {credit_score} is good, showing responsible credit management.",
        })
    elif credit_score >= 650:
        factor_details.append({
            "factor": "Credit Score",
            "value": credit_score,
            "impact": "neutral",
            "explanation": f"Your credit score of {credit_score} is fair. Improving this could result in better terms.",
        })
    else:
        factor_details.append({
            "factor": "Credit Score",
            "value": credit_score,
            "impact": "negative",
            "explanation": f"Your credit score of {credit_score} is below our typical threshold. This significantly impacts the decision.",
        })

    # DTI factor
    if dti_ratio <= 0.28:
        factor_details.append({
            "factor": "Debt-to-Income Ratio",
            "value": f"{dti_ratio*100:.1f}%",
            "impact": "positive",
            "explanation": f"Your DTI of {dti_ratio*100:.1f}% is excellent, well within guidelines.",
        })
    elif dti_ratio <= 0.36:
        factor_details.append({
            "factor": "Debt-to-Income Ratio",
            "value": f"{dti_ratio*100:.1f}%",
            "impact": "neutral",
            "explanation": f"Your DTI of {dti_ratio*100:.1f}% is acceptable but could be improved.",
        })
    else:
        factor_details.append({
            "factor": "Debt-to-Income Ratio",
            "value": f"{dti_ratio*100:.1f}%",
            "impact": "negative",
            "explanation": f"Your DTI of {dti_ratio*100:.1f}% exceeds our guideline of 43%. Paying down existing debt would help.",
        })

    # LTV factor
    if ltv_ratio <= 0.80:
        factor_details.append({
            "factor": "Loan-to-Value Ratio",
            "value": f"{ltv_ratio*100:.1f}%",
            "impact": "positive",
            "explanation": f"Your LTV of {ltv_ratio*100:.1f}% shows strong equity position.",
        })
    elif ltv_ratio <= 0.90:
        factor_details.append({
            "factor": "Loan-to-Value Ratio",
            "value": f"{ltv_ratio*100:.1f}%",
            "impact": "neutral",
            "explanation": f"Your LTV of {ltv_ratio*100:.1f}% is moderate. A larger down payment would improve this.",
        })
    else:
        factor_details.append({
            "factor": "Loan-to-Value Ratio",
            "value": f"{ltv_ratio*100:.1f}%",
            "impact": "negative",
            "explanation": f"Your LTV of {ltv_ratio*100:.1f}% is high, increasing lender risk. Mortgage insurance may be required.",
        })

    # Income verification
    if income_verified:
        factor_details.append({
            "factor": "Income Verification",
            "value": "Verified",
            "impact": "positive",
            "explanation": "Your income has been verified through official documentation.",
        })
    else:
        factor_details.append({
            "factor": "Income Verification",
            "value": "Not Verified",
            "impact": "negative",
            "explanation": "We were unable to verify your income. Please provide additional documentation.",
        })

    # Generate main explanation
    if decision == "auto_approve":
        explanation = (
            f"Congratulations! Your loan application has been automatically approved. "
            f"Your credit profile (score: {credit_score}, DTI: {dti_ratio*100:.1f}%) meets all our automated underwriting criteria. "
            f"You qualify for our best available rates."
        )
        adverse_action_reasons = []
        improvement_steps = []
    elif decision == "approve_with_conditions":
        explanation = (
            f"Your loan application has been approved with conditions. "
            f"While your overall profile is strong, we require additional steps before final approval."
        )
        adverse_action_reasons = []
        improvement_steps = [f"Additional documentation: {rf}" for rf in risk_factors]
    elif decision == "manual_underwriting_required":
        explanation = (
            f"Your application requires manual review by our underwriting team. "
            f"While your profile has some strengths, certain factors need human evaluation. "
            f"This typically takes 3-5 business days."
        )
        adverse_action_reasons = []
        improvement_steps = ["Wait for manual review decision", "Respond promptly to any document requests"]
    else:  # decline
        explanation = (
            f"We regret to inform you that your loan application cannot be approved at this time. "
            f"Based on our evaluation, the following factors contributed to this decision:"
        )
        adverse_action_reasons = []
        improvement_steps = []

        if credit_score < 650:
            adverse_action_reasons.append(f"Credit score ({credit_score}) below minimum requirement (620)")
            improvement_steps.append("Work on improving your credit score by paying bills on time and reducing debt")
        if dti_ratio > 0.43:
            adverse_action_reasons.append(f"Debt-to-income ratio ({dti_ratio*100:.1f}%) exceeds maximum (43%)")
            improvement_steps.append("Pay down existing debts to reduce your DTI ratio")
        if not income_verified:
            adverse_action_reasons.append("Unable to verify stated income")
            improvement_steps.append("Provide additional income documentation (W-2s, tax returns, paystubs)")

    # ECOA compliance notice
    ecoa_notice = ""
    if decision == "decline":
        ecoa_notice = (
            "Under the Equal Credit Opportunity Act (ECOA), you have the right to: "
            "1) Request the specific reasons for this decision within 60 days. "
            "2) Request a copy of your credit report used in this decision. "
            "3) Dispute any inaccurate information in your credit report. "
            "Contact us at [compliance email/phone] for more information."
        )

    result = {
        "explanation_id": str(uuid.uuid4()),
        "application_id": application_id,
        "decision": decision,
        "explanation": explanation,
        "factor_details": factor_details,
        "adverse_action_reasons": adverse_action_reasons,
        "improvement_steps": improvement_steps,
        "ecoa_notice": ecoa_notice,
        "requires_adverse_action_notice": decision == "decline",
        "compliance_status": "compliant" if decision != "decline" or ecoa_notice else "needs_review",
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info("Decision explanation generated: decision=%s, factors=%d", decision, len(factor_details))
    return result
