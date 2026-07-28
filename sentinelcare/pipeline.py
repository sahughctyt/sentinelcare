"""
run_pipeline(): chains IntakeAgent -> RiskAgent -> ReferralAgent -> FollowupAgent
into a single call.

Every dependency (DL models, the referral agent) is injected with a mock
default, so this runs end-to-end today with dummy data, and later takes real
components with no change to this function:

    run_pipeline(raw_intake, symptom_model=RealSymptomModel(), image_model=RealImageModel())
"""

from __future__ import annotations

from typing import Any

from agents import FollowupAgent, IntakeAgent, ReferralAgent, RiskAgent
from models import MockImageRiskModel, MockSymptomRiskModel


def run_pipeline(
    intake_data: dict[str, Any],
    symptom_model: Any = None,
    image_model: Any = None,
    referral_agent: ReferralAgent | None = None,
    followup_agent: FollowupAgent | None = None,
) -> dict[str, Any]:
    patient = IntakeAgent().process(intake_data)

    risk_agent = RiskAgent(
        symptom_model=symptom_model or MockSymptomRiskModel(),
        image_model=image_model or MockImageRiskModel(),
    )
    risk_assessment = risk_agent.assess(patient)

    referral_note = (referral_agent or ReferralAgent()).generate(patient, risk_assessment)
    followup_message = (followup_agent or FollowupAgent()).generate(
        patient, risk_assessment["risk_tier"]
    )

    return {
        "patient_id": patient["patient_id"],
        "risk_tier": risk_assessment["risk_tier"],
        "risk_details": risk_assessment,
        "referral_note": referral_note,
        "followup_message": followup_message,
    }
