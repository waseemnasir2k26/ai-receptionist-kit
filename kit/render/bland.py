"""Bland shape: one call/agent request body with custom tools and a transfer number."""
from __future__ import annotations

from . import common


def render(intake: dict) -> dict:
    url = intake["booking"].get("webhook_url") or "https://your-n8n-host.example.com/webhook/receptionist-tools"
    langs = intake["languages"]
    custom = []
    for t in common.tools(intake):
        if t["name"] == "transfer_to_human":
            continue  # Bland transfers through transfer_phone_number below
        custom.append({
            "name": t["name"], "description": t["description"], "url": url, "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"tool": t["name"], "arguments": "{{input}}"},
            "input_schema": t["parameters"],
            "response": {},
        })
    return {
        "task": common.prompt(intake),
        "first_sentence": common.first_message(intake),
        "voice": "REPLACE_WITH_VOICE",
        "language": "en-US" if langs == ["en"] else "babel",
        "model": "base",
        "record": intake["recording_consent"]["rule"] != "none",
        "max_duration": 15,
        "wait_for_greeting": False,
        "transfer_phone_number": intake["transfer_number"],
        "tools": custom,
        "metadata": common.metadata(intake),
    }
