"""Python reference of n8n/handler.js: tool-call responder returning {results:[{toolCallId,result}]}.

Demo logic only. Used for tests and as a template if you would rather host the webhook yourself.
Keep the result strings in sync with n8n/handler.js (a test compares them when node is installed).
"""
from __future__ import annotations

import json


def handle(name: str, args: dict) -> str:
    if name == "check_availability":
        svc = args.get("service_type") or "service"
        return f"Open windows for {svc}: morning and afternoon slots are available. Offer the caller at most two options."
    if name == "book_appointment":
        return f"Booking request recorded for {args.get('customer_name') or 'the caller'}. The team will confirm by text."
    if name == "transfer_to_human":
        return "Transfer requested."
    if name == "log_lead":
        return "Lead logged."
    return f"Unknown tool: {name}"


def respond(payload: dict) -> dict:
    body = payload.get("body", payload) if isinstance(payload, dict) else {}
    msg = body.get("message", body) if isinstance(body, dict) else {}
    calls = msg.get("toolCallList") if isinstance(msg.get("toolCallList"), list) else []
    if not calls and isinstance(msg.get("toolCalls"), list):
        calls = [{"id": c.get("id"), "name": (c.get("function") or {}).get("name"),
                  "arguments": (c.get("function") or {}).get("arguments")} for c in msg["toolCalls"]]
    results = []
    for c in calls:
        if not c or not c.get("id"):
            continue
        args = c.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                args = {}
        results.append({"toolCallId": c["id"], "result": handle(c.get("name"), args if isinstance(args, dict) else {})})
    return {"results": results}
