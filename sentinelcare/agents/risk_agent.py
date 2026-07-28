"""
RiskAgent: calls the two DL models and combines their outputs into one
final risk tier: Green, Yellow, or Red.

Takes model objects via the constructor (dependency injection) so mock models
can be swapped for the real ones later without touching this class:

    RiskAgent(symptom_model=RealSymptomModel(), image_model=RealImageModel())
"""

from __future__ import annotations

from typing import Any, Protocol


class RiskModel(Protocol):
    def predict(self, *args: Any, **kwargs: Any) -> float | None: ...


class RiskAgent:
    GREEN_MAX = 0.34
    YELLOW_MAX = 0.66

    def __init__(
        self,
        symptom_model: RiskModel,
        image_model: RiskModel,
        symptom_weight: float = 0.6,
        image_weight: float = 0.4,
    ) -> None:
        self.symptom_model = symptom_model
        self.image_model = image_model
        self.symptom_weight = symptom_weight
        self.image_weight = image_weight

    def assess(self, patient: dict[str, Any]) -> dict[str, Any]:
        symptom_score = self.symptom_model.predict(patient.get("symptoms", []))

        image_score = None
        if patient.get("photo_path"):
            image_score = self.image_model.predict(patient["photo_path"])

        combined_score = self._combine(symptom_score, image_score)
        risk_tier = self._tier_from_score(combined_score)

        return {
            "symptom_score": symptom_score,
            "image_score": image_score,
            "combined_score": round(combined_score, 2),
            "risk_tier": risk_tier,
        }

    def _combine(self, symptom_score: float | None, image_score: float | None) -> float:
        symptom_score = symptom_score or 0.0
        if image_score is None:
            # No photo provided (or model couldn't process it) — risk rests
            # entirely on the symptom model.
            return symptom_score
        return (symptom_score * self.symptom_weight) + (image_score * self.image_weight)

    def _tier_from_score(self, score: float) -> str:
        if score <= self.GREEN_MAX:
            return "Green"
        if score <= self.YELLOW_MAX:
            return "Yellow"
        return "Red"
