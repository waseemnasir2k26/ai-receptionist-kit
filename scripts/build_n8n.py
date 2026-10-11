"""Regenerates n8n/booking-webhook.json from n8n/handler.js so the two never drift."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
js = (root / "n8n" / "handler.js").read_text(encoding="utf-8")
wf = {
    "name": "AI Receptionist - tool-call responder (demo)",
    "nodes": [
        {"parameters": {"httpMethod": "POST", "path": "receptionist-tools", "responseMode": "responseNode", "options": {}},
         "id": "a1f0c2d4-0001-4000-8000-000000000001", "name": "Tool call webhook",
         "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0], "webhookId": "receptionist-tools"},
        {"parameters": {"jsCode": js},
         "id": "a1f0c2d4-0002-4000-8000-000000000002", "name": "Handle tool calls",
         "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [240, 0]},
        {"parameters": {"respondWith": "firstIncomingItem", "options": {}},
         "id": "a1f0c2d4-0003-4000-8000-000000000003", "name": "Respond with results",
         "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [480, 0]},
        {"parameters": {"content": "DEMO responder. Replace handle() in the Code node with your calendar / CRM calls. "
                                   "Returns {results:[{toolCallId,result}]}. Built with ai-receptionist-kit (SkynetLabs).",
                        "height": 120, "width": 360},
         "id": "a1f0c2d4-0004-4000-8000-000000000004", "name": "Read me",
         "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, -160]},
    ],
    "connections": {
        "Tool call webhook": {"main": [[{"node": "Handle tool calls", "type": "main", "index": 0}]]},
        "Handle tool calls": {"main": [[{"node": "Respond with results", "type": "main", "index": 0}]]},
    },
    "active": False,
    "settings": {"executionOrder": "v1"},
    "meta": {"built_with": "ai-receptionist-kit (SkynetLabs)"},
}
(root / "n8n" / "booking-webhook.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote n8n/booking-webhook.json")
