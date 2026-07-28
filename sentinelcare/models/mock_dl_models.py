"""
Stand-ins for the two real DL models (owned by teammate Seeya).

Contract these mocks must satisfy, so the real models drop in with zero
changes to RiskAgent or the pipeline:

    predict(...) -> float   # a risk score in [0.0, 1.0], higher = riskier

Once the real models are ready, swap them in via dependency injection:

    from real_models import SymptomClassifier, SkinLesionClassifier
    pipeline_result = run_pipeline(
        raw_intake,
        symptom_model=SymptomClassifier(),
        image_model=SkinLesionClassifier(),
    )

No other code needs to change.
"""

from __future__ import annotations

import hashlib


class MockSymptomRiskModel:
    """Fakes a symptom-based risk classifier using keyword heuristics."""

    HIGH_RISK_KEYWORDS = {
        "chest pain",
        "difficulty breathing",
        "shortness of breath",
        "severe bleeding",
        "unconscious",
        "unresponsive",
        "stroke",
        "seizure",
        "slurred speech",
        "confusion",
    }

    MODERATE_RISK_KEYWORDS = {
        "fever",
        "high fever",
        "persistent cough",
        "vomiting",
        "dehydration",
        "abdominal pain",
        "dizziness",
        "rash spreading",
    }

    def predict(self, symptoms: list[str]) -> float:
        if not symptoms:
            return 0.05

        text = " ".join(symptoms)
        score = 0.15

        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in text:
                score = max(score, 0.85)

        for keyword in self.MODERATE_RISK_KEYWORDS:
            if keyword in text:
                score = max(score, 0.5)

        # Multiple moderate-or-worse symptoms compound the risk slightly.
        score = min(1.0, score + 0.03 * max(0, len(symptoms) - 1))
        return round(score, 2)


class MockImageRiskModel:
    """Fakes an image-based risk classifier (e.g. wound/rash severity)."""

    def predict(self, photo_path: str | None) -> float | None:
        if not photo_path:
            return None
        # Deterministic pseudo-score so demo runs are repeatable, standing in
        # for what would be a real CNN inference call.
        digest = hashlib.md5(photo_path.encode("utf-8")).hexdigest()
        return round((int(digest, 16) % 100) / 100, 2)
