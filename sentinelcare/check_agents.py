"""One-off sanity check for each agent in isolation. Not part of the app - safe to delete."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from agents.intake_agent import IntakeAgent
from agents.risk_agent import RiskAgent
from agents.referral_agent import ReferralAgent
from agents.followup_agent import FollowupAgent
from models.mock_dl_models import MockSymptomRiskModel, MockImageRiskModel


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    return condition


all_ok = True

# --- IntakeAgent ---
print("\n== IntakeAgent ==")
intake = IntakeAgent()

p1 = intake.process({"name": "  Asha Rao ", "age": "29", "symptoms": "Fever, Cough, cough", "photo_path": ""})
all_ok &= check("trims name", p1["name"] == "Asha Rao")
all_ok &= check("parses string age to int", p1["age"] == 29)
all_ok &= check("splits/lowercases/dedupes symptoms", p1["symptoms"] == ["fever", "cough"])
all_ok &= check("blank photo_path -> None", p1["photo_path"] is None)
all_ok &= check("patient_id auto-generated", p1["patient_id"].startswith("PT-"))
all_ok &= check("no missing_fields when all present", p1["missing_fields"] == [])

p2 = intake.process({"symptoms": ["headache"]})
all_ok &= check("missing name/age flagged", set(p2["missing_fields"]) == {"name", "age"})
all_ok &= check("default name is Unknown", p2["name"] == "Unknown")

p3 = intake.process({"name": "X", "age": 999, "symptoms": []})
all_ok &= check("out-of-range age rejected -> None", p3["age"] is None)

# --- RiskAgent ---
print("\n== RiskAgent ==")
risk_agent = RiskAgent(MockSymptomRiskModel(), MockImageRiskModel())

green = risk_agent.assess({"symptoms": ["mild headache"], "photo_path": None})
all_ok &= check("mild symptoms, no photo -> Green", green["risk_tier"] == "Green")
all_ok &= check("no photo -> image_score is None", green["image_score"] is None)

red = risk_agent.assess({"symptoms": ["chest pain", "difficulty breathing"], "photo_path": None})
all_ok &= check("severe symptoms -> Red", red["risk_tier"] == "Red")

with_photo = risk_agent.assess({"symptoms": ["fever"], "photo_path": "uploads/a.jpg"})
all_ok &= check("photo present -> image_score populated", with_photo["image_score"] is not None)
all_ok &= check(
    "combined_score is weighted average",
    with_photo["combined_score"]
    == round(with_photo["symptom_score"] * 0.6 + with_photo["image_score"] * 0.4, 2),
)

# --- ReferralAgent ---
print("\n== ReferralAgent ==")
referral_agent = ReferralAgent()
print(f"  client initialized (real API key detected): {referral_agent.client is not None}")
note = referral_agent.generate(p1, green)
all_ok &= check("returns non-empty string", isinstance(note, str) and len(note) > 0)
print(f"  sample note: {note}")

broken_agent = ReferralAgent(api_key="gsk_invalid-key-for-testing")
note2 = broken_agent.generate(p1, green)
all_ok &= check("falls back gracefully on bad key / API error", note2.startswith("[Auto-generated"))

# --- FollowupAgent ---
print("\n== FollowupAgent ==")
followup_agent = FollowupAgent()
all_ok &= check("Green -> reminder message", followup_agent.generate(p1, "Green") is not None)
all_ok &= check("Yellow -> reminder message", followup_agent.generate(p1, "Yellow") is not None)
all_ok &= check("Red -> no followup (None)", followup_agent.generate(p1, "Red") is None)

print("\n" + ("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"))
