# SentinelCare — Thinking Layer

The AI agent chain that turns raw patient intake into a doctor-ready action:
`IntakeAgent -> RiskAgent -> ReferralAgent -> FollowupAgent`, wired together by
`run_pipeline()`. Plain Python classes, no agent framework.

## Setup

```
cd sentinelcare
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then paste in your GROQ_API_KEY
python main.py
```

`main.py` runs 3 sample patients (Green/Yellow/Red) through the full pipeline
and prints the result as JSON. It works with **no API key set** — `ReferralAgent`
falls back to a template note if `GROQ_API_KEY` is missing or the API call
fails, so the demo never breaks on stage.

## How it fits together

```python
from pipeline import run_pipeline

result = run_pipeline({
    "name": "Asha Rao",
    "age": 29,
    "symptoms": "fever, persistent cough",
    "photo_path": "uploads/asha.jpg",   # optional
})
# result = {patient_id, risk_tier, risk_details, referral_note, followup_message}
```

## Swapping in real components (this is the "dynamic" part)

Everything downstream of intake is dependency-injected, so nothing else needs
to change when the real pieces are ready:

**Real DL models from Seeya** — as soon as her models expose a `predict()`
method returning a risk score in `[0.0, 1.0]`:

```python
from real_models import SymptomClassifier, ImageClassifier

run_pipeline(raw_intake, symptom_model=SymptomClassifier(), image_model=ImageClassifier())
```

Until then, `models/mock_dl_models.py` provides `MockSymptomRiskModel` /
`MockImageRiskModel` as drop-in stand-ins with the same interface.

**Real patient data** — `run_pipeline()` takes the same raw dict shape
whether it comes from `SAMPLE_PATIENTS` in `main.py` or a real intake form/API;
`IntakeAgent` normalizes messy input (string or list symptoms, string or int
age, missing fields) either way.

**LLM API key** — `ReferralAgent` picks up `GROQ_API_KEY` (and optionally
`GROQ_MODEL`) from the environment automatically (via `.env`). No code
change needed to go from mock fallback notes to real Groq-generated ones.
See [WALKTHROUGH.md](WALKTHROUGH.md) for details and where to change things.

## Risk tiers

`RiskAgent` combines the symptom score and image score (60/40 weighted, or
100% symptom score if no photo) into: `Green` (≤0.34), `Yellow` (≤0.66), `Red`
(>0.66). Thresholds and weights are constructor args on `RiskAgent` if they
need tuning against real model output.
