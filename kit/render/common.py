"""Platform-neutral pieces: prompt text, first message, tool schemas, metadata."""
from __future__ import annotations

import re
from pathlib import Path

from .. import BUILT_WITH, __version__
from ..intake import DAYS, DAY_NAMES, derive

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "prompt.md.tmpl"
LANG_NAMES = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese", "it": "Italian",
              "ar": "Arabic", "hi": "Hindi", "ur": "Urdu", "zh": "Chinese"}


def _fill(template: str, values: dict) -> str:
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise KeyError(f"template variable '{key}' has no value")
        return values[key]
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", sub, template)


def _hours_lines(weekly: dict) -> str:
    out = []
    for d in DAYS:
        v = weekly[d]
        out.append(f"  - {DAY_NAMES[d]}: {v.replace('-', ' to ') if v else 'closed'}")
    return "\n".join(out)


def consent_sentence(intake: dict) -> str | None:
    rule = intake["recording_consent"]["rule"]
    if rule == "two_party":
        return "This call may be recorded for quality and scheduling."
    return None


def first_message(intake: dict) -> str:
    name = intake["business_name"].rstrip()
    parts = [f"Thanks for calling {name}{'' if name.endswith('.') else '.'}",
             f"This is {intake['agent_name']}, the AI receptionist."]
    c = consent_sentence(intake)
    if c:
        parts.append(c)
    parts.append("How can I help you today?")
    return " ".join(parts)


def prompt(intake: dict) -> str:
    d = derive(intake)
    rc = intake["recording_consent"]
    langs = intake["languages"]

    if rc["rule"] == "two_party":
        consent_block = (f"Recording consent rule for this business ({rc['region']}): all parties must consent. "
                         "The opening greeting already says the call may be recorded. If the caller objects, say you will "
                         "connect them to the team and call transfer_to_human.")
    elif rc["rule"] == "one_party":
        consent_block = (f"Recording consent rule for this business ({rc['region']}): one-party consent. "
                         "If the caller asks whether the call is recorded, answer honestly: it may be recorded for quality.")
    else:
        consent_block = "Calls are not recorded. If asked, say so."

    if len(langs) > 1:
        names = ", ".join(LANG_NAMES.get(x, x) for x in langs)
        language_block = (f"- Supported languages: {names}. Reply in the caller's language when it is one of these. "
                         "Otherwise continue in English and offer to have the team call back.")
    else:
        language_block = "- Speak English only. If the caller needs another language, offer to have the team call back."

    zips = intake["service_area_zips"]
    if d["capture_address"]:
        service_area_line = f"- Service area ZIP codes: {', '.join(zips)}"
        capture_line = ("Always capture: the caller's full name, a callback phone number, and the service address. "
                        "Confirm each back to the caller.")
        service_area_rule = ("Ask for the ZIP code of the service address. If it is not in the service area list, say politely "
                             "that you cannot serve that area. Do not book it.")
    else:
        service_area_line = "- Visits happen at the practice. Do not ask for a home address."
        capture_line = ("Always capture: the caller's full name, a callback phone number, whether they are a new or existing patient, "
                        "and the reason for the visit. Confirm each back to the caller.")
        service_area_rule = ""

    qq = intake["qualifying_questions"]
    qualifying_block = ("Ask these qualifying questions when they apply:\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(qq, 1))) if qq else ""

    method = intake["booking"]["method"]
    if method == "webhook":
        booking_block = ("For routine requests, call check_availability with the service type and preferred date. Offer at most two options. "
                         "When the caller picks one, call book_appointment, then read the booking back. "
                         "Always call log_lead before ending a call that did not end in a booking or a transfer.")
    elif method == "calendar_link":
        booking_block = ("You cannot book directly. Collect the details above, call log_lead with call_type \"new_lead\", "
                         "and tell the caller a team member will text them a booking link.")
    else:
        booking_block = ("You cannot book directly. Collect the details above and the caller's preferred days. Call log_lead with "
                         "call_type \"new_lead\" and tell the caller the team will call to confirm.")

    if intake["price_policy"] == "never":
        price_block = ("Never state, estimate, or hint at prices, fees, or ranges, even if the caller pushes. "
                       "Say the team gives an exact quote once they have assessed the job.")
    else:
        rng = "\n".join(f"- {x}" for x in intake["price_ranges"])
        price_block = ("You may share only the ranges below, and always call them ranges, not quotes. Never give an exact quote. "
                       "For anything else say the team quotes after assessing the job.\n" + rng)

    if d["medical_guardrail"]:
        medical_block = ("\n# Medical boundaries\nYou are not a clinician. Do not give medical or dental advice, diagnoses, or medication guidance. "
                         "For symptoms, collect details and follow the emergency rules. If swelling affects breathing or swallowing, "
                         "tell the caller to call 911.\n")
    else:
        medical_block = ""

    safety = (intake["emergency"].get("safety_script") or "").strip()
    safety_step = f"Say: \"{safety}\"" if safety else "Tell the caller to call 911 if anyone is in immediate danger."

    faq_block = "\n".join(f"- Q: {f['q']}\n  A: {f['a']}" for f in intake["faqs"]) or "- No FAQs configured."

    values = {
        "agent_name": intake["agent_name"], "business_name": intake["business_name"],
        "trade_article": d["trade_article"], "trade_label": d["trade_label"],
        "language_block": language_block, "timezone": intake["hours"]["timezone"],
        "hours_lines": _hours_lines(intake["hours"]["weekly"]), "service_area_line": service_area_line,
        "service_types": ", ".join(intake["service_types"]), "consent_block": consent_block,
        "emergency_keywords": "; ".join(intake["emergency"]["keywords"]), "safety_step": safety_step,
        "capture_line": capture_line, "service_area_rule": service_area_rule, "qualifying_block": qualifying_block,
        "booking_block": booking_block, "price_block": price_block, "medical_block": medical_block, "faq_block": faq_block,
    }
    text = _fill(TEMPLATE.read_text(encoding="utf-8"), values)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _urgency():
    return {"type": "string", "enum": ["routine", "urgent", "emergency"]}


def tools(intake: dict) -> list[dict]:
    """Platform-neutral tool schemas: name, description, JSON-schema parameters."""
    addr = derive(intake)["capture_address"]
    book_props = {
        "customer_name": {"type": "string", "description": "Caller's full name"},
        "phone": {"type": "string", "description": "Callback phone number"},
        "service_type": {"type": "string", "description": "What the visit is for"},
        "start_time": {"type": "string", "description": "Chosen slot, ISO 8601 with offset"},
        "urgency": _urgency(),
        "notes": {"type": "string", "description": "Anything else the team should know"},
    }
    book_req = ["customer_name", "phone", "service_type", "start_time"]
    lead_props = {
        "caller_name": {"type": "string"},
        "phone": {"type": "string"},
        "service_type": {"type": "string"},
        "urgency": _urgency(),
        "call_type": {"type": "string", "enum": ["new_lead", "existing_customer", "emergency", "spam_or_wrong_number", "other"]},
        "after_hours": {"type": "boolean", "description": "True when the call came outside opening hours"},
        "summary": {"type": "string", "description": "One or two sentences on what the caller needs"},
    }
    avail_props = {
        "service_type": {"type": "string"},
        "preferred_date": {"type": "string", "description": "ISO date, e.g. 2026-03-14"},
    }
    if addr:
        book_props["service_address"] = {"type": "string", "description": "Street address of the job"}
        book_req.append("service_address")
        lead_props["address"] = {"type": "string"}
        avail_props["zip"] = {"type": "string", "description": "ZIP or postal code of the job"}
    else:
        book_props["patient_status"] = {"type": "string", "enum": ["new", "existing"]}
        lead_props["patient_status"] = {"type": "string", "enum": ["new", "existing"]}
    return [
        {"name": "check_availability", "description": "Look up open appointment slots for a service. Read-only.",
         "parameters": {"type": "object", "properties": avail_props, "required": ["service_type"]}},
        {"name": "book_appointment", "description": "Book an appointment in the chosen slot after the caller has confirmed it.",
         "parameters": {"type": "object", "properties": book_props, "required": book_req}},
        {"name": "transfer_to_human", "description": "Transfer the live call to a person. Use for emergencies, requests for a human, or anything out of scope.",
         "parameters": {"type": "object", "properties": {
             "reason": {"type": "string", "description": "Why the call is being transferred"},
             "urgency": _urgency(),
             "summary": {"type": "string", "description": "One-sentence handoff note"}}, "required": ["reason"]}},
        {"name": "log_lead", "description": "Record the call outcome and caller details for the team to follow up. Call before ending any call that was not booked or transferred.",
         "parameters": {"type": "object", "properties": lead_props, "required": ["call_type", "summary"]}},
    ]


def metadata(intake: dict) -> dict:
    return {
        "built_with": BUILT_WITH,
        "kit_version": __version__,
        "trade": intake["trade"],
        "price_policy": intake["price_policy"],
        "recording_rule": intake["recording_consent"]["rule"],
        "languages": intake["languages"],
    }
