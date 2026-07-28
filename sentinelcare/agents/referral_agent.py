"""
ReferralAgent: turns a risk tier + patient data into a short, doctor-readable
referral note (2-3 sentences) using the Groq API.

Falls back to a template-based note (no network call) whenever GROQ_API_KEY
isn't set, or if the API call fails for any reason. This means the rest of
the pipeline is fully runnable offline while the real key is being sorted
out, and it degrades gracefully in a live demo instead of crashing.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - groq is in requirements.txt
    Groq = None  # type: ignore[assignment, misc]

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class ReferralAgent:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.model = model or os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
        self.client = None

        key = api_key or os.environ.get("GROQ_API_KEY")
        if key and Groq is not None:
            self.client = Groq(api_key=key)

    def generate(self, patient: dict[str, Any], risk_assessment: dict[str, Any]) -> str:
        if self.client is None:
            return self._fallback_note(patient, risk_assessment)

        prompt = self._build_prompt(patient, risk_assessment)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:
            return self._fallback_note(patient, risk_assessment)

        note = response.choices[0].message.content if response.choices else None
        if note and note.strip():
            return note.strip()

        return self._fallback_note(patient, risk_assessment)

    @staticmethod
    def _build_prompt(patient: dict[str, Any], risk_assessment: dict[str, Any]) -> str:
        symptoms = ", ".join(patient.get("symptoms", [])) or "no symptoms recorded"
        return (
            "You are assisting a primary care doctor triaging patients. "
            "Write a referral note of 2-3 sentences for the doctor based on "
            "the intake data below. Be factual and clinical, do not diagnose, "
            "and do not add any greeting or sign-off — output only the note.\n\n"
            f"Patient: {patient.get('name', 'Unknown')}, age {patient.get('age', 'unknown')}\n"
            f"Reported symptoms: {symptoms}\n"
            f"Risk tier (from AI triage models): {risk_assessment.get('risk_tier')}\n"
            f"Combined risk score: {risk_assessment.get('combined_score')}"
        )

    @staticmethod
    def _fallback_note(patient: dict[str, Any], risk_assessment: dict[str, Any]) -> str:
        symptoms = ", ".join(patient.get("symptoms", [])) or "no symptoms recorded"
        tier = risk_assessment.get("risk_tier", "Unknown")
        return (
            f"[Auto-generated, LLM unavailable] Patient {patient.get('name', 'Unknown')} "
            f"(age {patient.get('age', 'unknown')}) presented with: {symptoms}. "
            f"AI triage flagged this as {tier} risk (score {risk_assessment.get('combined_score')}). "
            "Please review and confirm next steps."
        )
