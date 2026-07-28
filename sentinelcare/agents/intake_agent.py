"""
IntakeAgent: turns raw, messy form data into a consistent patient record.

Real-world intake forms are inconsistent (symptoms as a comma string vs a list,
age as "45" vs 45, missing photo, etc). This agent's only job is to normalize
that into one predictable shape so every downstream agent can rely on it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class IntakeAgent:
    """Cleans and structures raw patient intake data."""

    def process(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        name = self._clean_name(raw_data.get("name"))
        age = self._clean_age(raw_data.get("age"))
        symptoms = self._clean_symptoms(raw_data.get("symptoms"))
        photo_path = self._clean_photo_path(raw_data.get("photo_path"))

        missing_fields = [
            field
            for field, value in (("name", name), ("age", age), ("symptoms", symptoms))
            if not value
        ]

        return {
            "patient_id": raw_data.get("patient_id") or f"PT-{uuid.uuid4().hex[:8].upper()}",
            "name": name or "Unknown",
            "age": age,
            "symptoms": symptoms,
            "photo_path": photo_path,
            "missing_fields": missing_fields,
            "intake_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _clean_name(name: Any) -> str | None:
        if not isinstance(name, str):
            return None
        cleaned = name.strip()
        return cleaned or None

    @staticmethod
    def _clean_age(age: Any) -> int | None:
        if isinstance(age, bool):
            return None
        if isinstance(age, int):
            return age if 0 <= age <= 130 else None
        if isinstance(age, str):
            digits = "".join(ch for ch in age if ch.isdigit())
            if digits:
                value = int(digits)
                return value if 0 <= value <= 130 else None
        return None

    @staticmethod
    def _clean_symptoms(symptoms: Any) -> list[str]:
        if symptoms is None:
            return []
        if isinstance(symptoms, str):
            parts = symptoms.split(",")
        elif isinstance(symptoms, (list, tuple, set)):
            parts = list(symptoms)
        else:
            return []

        cleaned: list[str] = []
        seen: set[str] = set()
        for part in parts:
            text = str(part).strip().lower()
            if text and text not in seen:
                seen.add(text)
                cleaned.append(text)
        return cleaned

    @staticmethod
    def _clean_photo_path(photo_path: Any) -> str | None:
        if isinstance(photo_path, str) and photo_path.strip():
            return photo_path.strip()
        return None
