# SentinelCare — Walkthrough

What this is, how data flows through it, and exactly where to go when you
need to change something.

## 1. The big picture

One function ties everything together:

```
run_pipeline(raw_intake_dict)
    -> IntakeAgent    cleans raw form data
    -> RiskAgent      calls 2 DL models, produces a risk tier
    -> ReferralAgent  asks an LLM to write a doctor-readable note
    -> FollowupAgent  writes a reminder text (skipped for Red tier)
    -> returns one dict with everything
```

Each stage is a plain class with one main method. No framework, no hidden
state — you can read any single agent file top to bottom in under a minute.

## 2. File map

```
sentinelcare/
  agents/
    intake_agent.py     -> IntakeAgent
    risk_agent.py        -> RiskAgent
    referral_agent.py    -> ReferralAgent  (the one that calls an LLM)
    followup_agent.py    -> FollowupAgent
  models/
    mock_dl_models.py    -> MockSymptomRiskModel, MockImageRiskModel
                             (stand-ins for Seeya's real models)
  pipeline.py             -> run_pipeline() — chains the 4 agents
  main.py                 -> demo script, run this to see it work
  check_agents.py         -> sanity-check script for all 4 agents
  .env                    -> your local secrets/config (never commit this)
  .env.example            -> template showing what .env needs
  requirements.txt        -> pip dependencies
```

## 3. Walking through one request

Say a form submits:

```python
{"name": "Vikram Singh", "age": 54, "symptoms": "fever, persistent cough, dehydration", "photo_path": "uploads/vikram_rash.jpg"}
```

**Step 1 — `IntakeAgent.process()`** ([agents/intake_agent.py](agents/intake_agent.py))
Turns that into a consistent record: trims the name, converts age to `int`,
splits/lowercases/dedupes the symptoms string into a list, generates a
`patient_id`, and records which fields were missing (if any) instead of
crashing on bad input.

```python
{"patient_id": "PT-693AC07E", "name": "Vikram Singh", "age": 54,
 "symptoms": ["fever", "persistent cough", "dehydration"],
 "photo_path": "uploads/vikram_rash.jpg", "missing_fields": [], "intake_timestamp": "..."}
```

**Step 2 — `RiskAgent.assess()`** ([agents/risk_agent.py](agents/risk_agent.py))
Calls `symptom_model.predict(symptoms)` and, if a photo exists,
`image_model.predict(photo_path)`. Combines them as
`0.6 * symptom_score + 0.4 * image_score` (or 100% symptom score if there's
no photo), then buckets the result:

| combined_score | tier |
|---|---|
| ≤ 0.34 | Green |
| ≤ 0.66 | Yellow |
| \> 0.66 | Red |

**Step 3 — `ReferralAgent.generate()`** ([agents/referral_agent.py](agents/referral_agent.py))
Builds a prompt from the patient + risk data and calls the **Groq API**
(`llama-3.3-70b-versatile` by default) for a 2-3 sentence referral note. If
there's no API key or the call fails for any reason, it falls back to a
template note instead of crashing — that's the
`[Auto-generated, LLM unavailable] ...` text you'll see when no key is
configured.

**Step 4 — `FollowupAgent.generate()`** ([agents/followup_agent.py](agents/followup_agent.py))
Returns a canned reminder string for `Green`/`Yellow`, or `None` for `Red`
(a Red patient is being referred now, not reminded later).

**Result:**

```python
{"patient_id": ..., "risk_tier": "Yellow", "risk_details": {...},
 "referral_note": "...", "followup_message": "..."}
```

## 4. Running it

```
cd sentinelcare
.venv\Scripts\activate
python main.py             # runs 3 sample patients end-to-end
python check_agents.py     # runs isolated checks on all 4 agents
```

With `GROQ_API_KEY` set in `.env`, both scripts use real Groq-generated
referral notes. Without it, they fall back to template notes instead of
crashing.

## 5. Where to change things

| I want to... | Change this |
|---|---|
| Change how raw intake fields are parsed/validated | `agents/intake_agent.py` — one static method per field (`_clean_name`, `_clean_age`, `_clean_symptoms`, `_clean_photo_path`) |
| Add a new intake field (e.g. `phone`, `location`) | Add a `_clean_*` method in `intake_agent.py`, add it to the returned dict in `process()` |
| Plug in the **real** DL models | Nothing in `risk_agent.py` needs to change — just pass real model objects into `run_pipeline()` (see §6 below) |
| Change the Green/Yellow/Red thresholds or the 60/40 weighting | `agents/risk_agent.py` — `GREEN_MAX`, `YELLOW_MAX`, `symptom_weight`, `image_weight` (all constructor args, so callers can override without editing the file) |
| Change the referral note's wording/length/tone | `agents/referral_agent.py` — `_build_prompt()` |
| Change the Groq model | `.env` — `GROQ_MODEL` (or `DEFAULT_MODEL` in `referral_agent.py` if no env var is set) |
| Switch LLM provider entirely (e.g. to local Ollama) | `agents/referral_agent.py` — swap the `Groq(...)` client + `chat.completions.create(...)` call; `generate()`'s signature and the rest of the pipeline don't need to change |
| Change the fallback note (used when the LLM is unavailable) | `agents/referral_agent.py` — `_fallback_note()` |
| Change the reminder text for Green/Yellow | `agents/followup_agent.py` |
| Change the order or wiring of the 4 agents | `pipeline.py` — `run_pipeline()` |
| Add a 5th agent to the chain | Create `agents/your_agent.py`, add it to `agents/__init__.py`, call it from `run_pipeline()` in `pipeline.py` |

## 6. Swapping in the real DL models (Seeya's work)

`run_pipeline()` takes the models as arguments — mocks are only the default:

```python
from pipeline import run_pipeline
from real_models import SymptomClassifier, ImageClassifier   # her real code

result = run_pipeline(
    raw_intake,
    symptom_model=SymptomClassifier(),
    image_model=ImageClassifier(),
)
```

The only requirement on her side: each model needs a `predict(...)` method
that returns a float between `0.0` and `1.0` (higher = riskier). That's the
entire contract — `RiskAgent` doesn't care how the score was produced.
`models/mock_dl_models.py` is just today's stand-in for that same interface.

## 7. LLM backend: Groq

`ReferralAgent` calls the Groq API (`.env` → `GROQ_API_KEY`, model from
`GROQ_MODEL` or `llama-3.3-70b-versatile` by default). `.env` also has
`LLM_BACKEND` / `LOCAL_LLM_URL` / `LOCAL_LLM_MODEL` entries for a local
Ollama server, but those aren't wired into the code — `ReferralAgent` only
knows about Groq today. If you want a local-model fallback (e.g. Groq is
down or you want to run fully offline), add an `LLM_BACKEND` check in
`referral_agent.py`'s `__init__` that calls `LOCAL_LLM_URL` with a plain
HTTP request instead of the Groq client — same `generate()` signature, same
fallback-on-failure behavior, nothing else in the pipeline changes.
