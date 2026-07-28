"""
Demo runner for the SentinelCare thinking layer.

Run with:
    python main.py

Works with no ANTHROPIC_API_KEY set (ReferralAgent falls back to a template
note). Set ANTHROPIC_API_KEY in a .env file (see .env.example) to see real
LLM-generated referral notes.
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from pipeline import run_pipeline

load_dotenv()

SAMPLE_PATIENTS = [
    {
        "name": "Asha Rao",
        "age": 29,
        "symptoms": "mild headache, runny nose",
        "photo_path": None,
    },
    {
        "name": "Vikram Singh",
        "age": 54,
        "symptoms": "fever, persistent cough, dehydration",
        "photo_path": "uploads/vikram_rash.jpg",
    },
    {
        "name": "Meera Iyer",
        "age": 67,
        "symptoms": "chest pain, difficulty breathing",
        "photo_path": None,
    },
]


def main() -> None:
    for raw_intake in SAMPLE_PATIENTS:
        result = run_pipeline(raw_intake)
        print("=" * 70)
        print(f"Patient: {raw_intake['name']}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
