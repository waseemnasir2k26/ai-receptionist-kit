"""Structural validator for n8n/booking-webhook.json. Offline; does not need n8n."""
from __future__ import annotations

import json
from pathlib import Path

WEBHOOK = "n8n-nodes-base.webhook"
CODE = "n8n-nodes-base.code"
RESPOND = "n8n-nodes-base.respondToWebhook"


def validate_workflow(wf) -> list[str]:
    e: list[str] = []
    if not isinstance(wf, dict):
        return ["workflow must be a JSON object"]
    nodes = wf.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return ["nodes: must be a non-empty list"]
    names = [n.get("name") for n in nodes]
    if len(set(names)) != len(names):
        e.append("nodes: duplicate node names")
    by_type = {}
    for n in nodes:
        for k in ("name", "type", "typeVersion", "position", "parameters"):
            if k not in n:
                e.append(f"node {n.get('name', '?')}: missing '{k}'")
        by_type.setdefault(n.get("type"), []).append(n)
    for t in (WEBHOOK, CODE, RESPOND):
        if t not in by_type:
            e.append(f"missing node of type {t}")
    if e:
        return e
    hook = by_type[WEBHOOK][0]["parameters"]
    if hook.get("httpMethod") != "POST":
        e.append("webhook: httpMethod must be POST")
    if not hook.get("path"):
        e.append("webhook: path is required")
    if hook.get("responseMode") != "responseNode":
        e.append("webhook: responseMode must be 'responseNode' so the Respond node replies")
    js = by_type[CODE][0]["parameters"].get("jsCode", "")
    for needle in ("toolCallId", "results", "toolCallList"):
        if needle not in js:
            e.append(f"code node: jsCode does not mention '{needle}'")
    conns = wf.get("connections", {})
    hook_name, code_name, resp_name = (by_type[t][0]["name"] for t in (WEBHOOK, CODE, RESPOND))

    def targets(src):
        return [c["node"] for outs in conns.get(src, {}).get("main", []) for c in outs]

    if code_name not in targets(hook_name):
        e.append("connections: webhook must connect to the code node")
    if resp_name not in targets(code_name):
        e.append("connections: code node must connect to the respond node")
    return e


def validate_file(path) -> list[str]:
    try:
        wf = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{path}: cannot read workflow ({exc})"]
    return validate_workflow(wf)
