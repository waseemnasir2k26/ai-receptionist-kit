"""Business intake: load presets, build a starter business.json, validate it."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

PRESET_DIR = Path(os.environ.get("AI_RECEPTIONIST_PRESETS") or Path(__file__).resolve().parent.parent / "presets")
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_NAMES = dict(zip(DAYS, ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")))
PRICE_POLICIES = ("never", "ranges")
BOOKING_METHODS = ("webhook", "calendar_link", "callback")
CONSENT_RULES = ("two_party", "one_party", "none")
TOP_KEYS = {"schema_version", "trade", "business_name", "agent_name", "hours", "service_area_zips", "emergency",
            "price_policy", "price_ranges", "booking", "transfer_number", "recording_consent", "languages",
            "faqs", "qualifying_questions", "service_types"}
PLACEHOLDER_WEBHOOK = "https://your-n8n-host.example.com/webhook/receptionist-tools"


class IntakeError(ValueError):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def list_presets() -> list[str]:
    return sorted(p.stem for p in PRESET_DIR.glob("*.json"))


def load_preset(name: str) -> dict:
    path = PRESET_DIR / f"{name}.json"
    if not path.is_file():
        raise IntakeError([f"trade: unknown preset '{name}' (available: {', '.join(list_presets())})"])
    return json.loads(path.read_text(encoding="utf-8"))


def from_preset(name: str, business_name: str | None = None) -> dict:
    p = load_preset(name)
    pretty = {"hvac": "HVAC"}.get(name, name.capitalize())
    return {
        "schema_version": 1,
        "trade": name,
        "business_name": business_name or f"Example {pretty} Co.",
        "agent_name": "Riley",
        "hours": {"timezone": "America/Chicago", "weekly": dict(p["hours"]["weekly"])},
        "service_area_zips": [] if name == "dental" else ["60601", "60602", "60603"],
        "emergency": {"keywords": list(p["emergency"]["keywords"]), "safety_script": p["emergency"]["safety_script"]},
        "price_policy": "never",
        "price_ranges": [],
        "booking": {"method": "webhook", "webhook_url": PLACEHOLDER_WEBHOOK},
        "transfer_number": "+15555550100",
        "recording_consent": {"region": "US (conservative: assume all-party consent)", "rule": "two_party"},
        "languages": ["en"],
        "faqs": [dict(f) for f in p["faqs"]],
        "qualifying_questions": list(p["qualifying_questions"]),
        "service_types": list(p["service_types"]),
    }


def derive(intake: dict) -> dict:
    """Fields computed from the trade preset, not stored in business.json."""
    p = load_preset(intake["trade"])
    return {
        "trade_label": p["trade_label"],
        "trade_article": p["trade_article"],
        "medical_guardrail": intake["trade"] == "dental",
        "capture_address": intake["trade"] != "dental",
    }


_HHMM = r"([01]\d|2[0-3]):[0-5]\d"
_RANGE = re.compile(rf"^({_HHMM})-({_HHMM})$")
_TZ = re.compile(r"^(UTC|[A-Za-z_]+/[A-Za-z_+\-0-9/]+)$")
_E164 = re.compile(r"^\+[1-9]\d{6,14}$")
_ZIP = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-]{1,9}$")


def _nonempty_str(v, maxlen=120):
    return isinstance(v, str) and 0 < len(v.strip()) <= maxlen


def validate(data) -> list[str]:
    """Return a list of 'path: message' strings. Empty list means valid."""
    e: list[str] = []
    if not isinstance(data, dict):
        return ["$: intake must be a JSON object"]
    for k in sorted(set(data) - TOP_KEYS):
        e.append(f"{k}: unknown key (typo?)")
    if data.get("schema_version") != 1:
        e.append("schema_version: must be 1")
    if data.get("trade") not in list_presets():
        e.append(f"trade: must be one of {', '.join(list_presets())}")
    if not _nonempty_str(data.get("business_name"), 80):
        e.append("business_name: required, 1-80 characters")
    if not _nonempty_str(data.get("agent_name"), 40):
        e.append("agent_name: required, 1-40 characters")

    hours = data.get("hours")
    if not isinstance(hours, dict):
        e.append("hours: must be an object with timezone and weekly")
    else:
        if not isinstance(hours.get("timezone"), str) or not _TZ.match(hours["timezone"]):
            e.append("hours.timezone: must be an IANA name such as America/Chicago, or UTC")
        weekly = hours.get("weekly")
        if not isinstance(weekly, dict) or set(weekly) != set(DAYS):
            e.append(f"hours.weekly: must have exactly the keys {', '.join(DAYS)}")
        else:
            open_days = 0
            for d in DAYS:
                v = weekly[d]
                if v is None:
                    continue
                m = _RANGE.match(v) if isinstance(v, str) else None
                if not m:
                    e.append(f"hours.weekly.{d}: must be null or 'HH:MM-HH:MM'")
                elif v.split("-")[0] >= v.split("-")[1]:
                    e.append(f"hours.weekly.{d}: opening time must be before closing time")
                else:
                    open_days += 1
            if open_days == 0:
                e.append("hours.weekly: at least one day must be open")

    zips = data.get("service_area_zips")
    if not isinstance(zips, list) or not all(isinstance(z, str) and _ZIP.match(z) for z in zips):
        e.append("service_area_zips: must be a list of ZIP/postal code strings")
    elif not zips and data.get("trade") != "dental":
        e.append("service_area_zips: at least one code is required for this trade")

    em = data.get("emergency")
    if not isinstance(em, dict):
        e.append("emergency: must be an object with keywords")
    else:
        kw = em.get("keywords")
        if not isinstance(kw, list) or not kw or not all(_nonempty_str(k, 120) for k in kw):
            e.append("emergency.keywords: must be a non-empty list of strings")
        if "safety_script" in em and not isinstance(em["safety_script"], str):
            e.append("emergency.safety_script: must be a string")

    pol = data.get("price_policy")
    if pol not in PRICE_POLICIES:
        e.append(f"price_policy: must be one of {', '.join(PRICE_POLICIES)}")
    elif pol == "ranges":
        pr = data.get("price_ranges")
        if not isinstance(pr, list) or not pr or not all(_nonempty_str(x, 160) for x in pr):
            e.append("price_ranges: required (non-empty list of strings) when price_policy is 'ranges'")

    b = data.get("booking")
    if not isinstance(b, dict) or b.get("method") not in BOOKING_METHODS:
        e.append(f"booking.method: must be one of {', '.join(BOOKING_METHODS)}")
    elif b["method"] == "webhook":
        url = b.get("webhook_url")
        if not isinstance(url, str) or not re.match(r"^https://[^\s/]+(/\S*)?$", url):
            e.append("booking.webhook_url: required https URL when method is 'webhook'")

    if not isinstance(data.get("transfer_number"), str) or not _E164.match(data["transfer_number"]):
        e.append("transfer_number: must be E.164, e.g. +15555550100")

    rc = data.get("recording_consent")
    if not isinstance(rc, dict) or rc.get("rule") not in CONSENT_RULES:
        e.append(f"recording_consent.rule: must be one of {', '.join(CONSENT_RULES)}")
    elif not _nonempty_str(rc.get("region"), 80):
        e.append("recording_consent.region: required free-text jurisdiction, e.g. 'US-CA'")

    langs = data.get("languages")
    if not isinstance(langs, list) or not langs or not all(isinstance(x, str) and re.match(r"^[a-z]{2}$", x) for x in langs):
        e.append("languages: must be a non-empty list of 2-letter codes, e.g. ['en','es']")
    elif langs[0] != "en" and "en" not in langs:
        e.append("languages: include 'en' (used as the fallback language)")

    faqs = data.get("faqs")
    if not isinstance(faqs, list) or not all(isinstance(f, dict) and _nonempty_str(f.get("q"), 200) and _nonempty_str(f.get("a"), 500) for f in faqs):
        e.append("faqs: must be a list of {q, a} objects with non-empty strings")
    qq = data.get("qualifying_questions")
    if not isinstance(qq, list) or not all(_nonempty_str(x, 200) for x in qq):
        e.append("qualifying_questions: must be a list of strings")
    st = data.get("service_types")
    if not isinstance(st, list) or not st or not all(_nonempty_str(x, 80) for x in st):
        e.append("service_types: must be a non-empty list of strings")
    return e


def load(path) -> dict:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise IntakeError([f"{p}: file not found"])
    except json.JSONDecodeError as exc:
        raise IntakeError([f"{p}: invalid JSON ({exc})"])
    errs = validate(data)
    if errs:
        raise IntakeError(errs)
    return data
