"""Retell shape: one JSON holding the Retell LLM object and the agent object."""
from __future__ import annotations

from . import common

PLACEHOLDER_VOICE = "REPLACE_WITH_VOICE_ID"


def render(intake: dict) -> dict:
    url = intake["booking"].get("webhook_url") or "https://your-n8n-host.example.com/webhook/receptionist-tools"
    langs = intake["languages"]
    general_tools = []
    for t in common.tools(intake):
        if t["name"] == "transfer_to_human":
            general_tools.append({
                "type": "transfer_call", "name": t["name"], "description": t["description"],
                "transfer_destination": {"type": "predefined", "number": intake["transfer_number"]},
                "transfer_option": {"type": "cold_transfer"},
            })
        else:
            general_tools.append({
                "type": "custom", "name": t["name"], "description": t["description"], "url": url,
                "speak_during_execution": False, "speak_after_execution": True,
                "parameters": t["parameters"],
            })
    general_tools.append({"type": "end_call", "name": "end_call", "description": "End the call once the caller is finished."})
    return {
        "llm": {
            "model": "gpt-4o",
            "general_prompt": common.prompt(intake),
            "begin_message": common.first_message(intake),
            "general_tools": general_tools,
        },
        "agent": {
            "agent_name": f"{intake['business_name']} - {intake['agent_name']}",
            "response_engine": {"type": "retell-llm", "llm_id": "REPLACE_WITH_LLM_ID"},
            "voice_id": PLACEHOLDER_VOICE,
            "language": "en-US" if langs == ["en"] else "multi",
            "max_call_duration_ms": 900000,
        },
        "metadata": common.metadata(intake),
    }
