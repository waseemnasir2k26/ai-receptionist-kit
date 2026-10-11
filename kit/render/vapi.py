"""Vapi assistant shape (see docs/platforms.md for the reference and review date)."""
from __future__ import annotations

from . import common

PLACEHOLDER_VOICE = "REPLACE_WITH_VOICE_ID"


def render(intake: dict) -> dict:
    url = intake["booking"].get("webhook_url") or "https://your-n8n-host.example.com/webhook/receptionist-tools"
    langs = intake["languages"]
    tool_list = []
    for t in common.tools(intake):
        if t["name"] == "transfer_to_human":
            tool_list.append({
                "type": "transferCall",
                "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]},
                "destinations": [{"type": "number", "number": intake["transfer_number"],
                                  "message": "Let me connect you with the team."}],
            })
        else:
            tool_list.append({
                "type": "function",
                "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]},
                "server": {"url": url},
            })
    return {
        "name": f"{intake['business_name']} - {intake['agent_name']} ({intake['trade']})"[:40],
        "firstMessage": common.first_message(intake),
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.3,
            "messages": [{"role": "system", "content": common.prompt(intake)}],
            "tools": tool_list,
        },
        "voice": {"provider": "11labs", "voiceId": PLACEHOLDER_VOICE},
        "transcriber": {"provider": "deepgram", "model": "nova-2", "language": "en" if langs == ["en"] else "multi"},
        "recordingEnabled": intake["recording_consent"]["rule"] != "none",
        "endCallFunctionEnabled": True,
        "maxDurationSeconds": 900,
        "metadata": common.metadata(intake),
    }
