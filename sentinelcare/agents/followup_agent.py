"""
FollowupAgent: generates a simulated reminder message for Green/Yellow tier
patients. Red tier patients are being referred immediately, so no follow-up
reminder is generated for them.

This is simulated only — it returns text, it never sends an SMS/IVR call.
"""

from __future__ import annotations

from typing import Any


class FollowupAgent:
    def generate(self, patient: dict[str, Any], risk_tier: str) -> str | None:
        name = patient.get("name", "Patient")

        if risk_tier == "Green":
            return (
                f"Hi {name}, this is a reminder from SentinelCare. Your symptoms were "
                "assessed as low risk. Please rest, stay hydrated, and check in with us "
                "in 7 days if you're still not feeling well."
            )

        if risk_tier == "Yellow":
            return (
                f"Hi {name}, this is a reminder from SentinelCare. Your symptoms need "
                "a closer follow-up. Please check in with a doctor within 2-3 days, or "
                "sooner if your symptoms get worse."
            )

        # Red tier -> immediate referral in progress, no delayed reminder needed.
        return None
