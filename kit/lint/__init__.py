"""Linter entry points: load a prompt or a rendered platform config, run the rules."""
from __future__ import annotations

import json
from pathlib import Path

from .rules import DEFAULT_MAX_CHARS, RULE_BY_ID, RULES, Doc, Finding


def detect_platform(cfg: dict) -> str | None:
    if "llm" in cfg and "agent" in cfg:
        return "retell"
    if isinstance(cfg.get("model"), dict) and "messages" in cfg["model"]:
        return "vapi"
    if ("task" in cfg or "prompt" in cfg) and ("first_sentence" in cfg or "tools" in cfg or "transfer_phone_number" in cfg):
        return "bland"
    return None


def doc_from_config(cfg: dict, source: str = "<config>") -> Doc:
    platform = detect_platform(cfg)
    if platform is None:
        raise ValueError("unrecognised config: expected a Vapi assistant, a Retell {llm, agent} object, or a Bland request body")
    if platform == "vapi":
        msgs = cfg["model"].get("messages") or []
        prompt = "\n".join(m.get("content", "") for m in msgs if m.get("role") == "system")
        first = cfg.get("firstMessage", "")
        tools = {(t.get("function") or {}).get("name") or t.get("name") for t in cfg["model"].get("tools", [])}
    elif platform == "retell":
        prompt = cfg["llm"].get("general_prompt", "")
        first = cfg["llm"].get("begin_message", "")
        tools = {t.get("name") for t in cfg["llm"].get("general_tools", [])}
    else:
        prompt = cfg.get("task") or cfg.get("prompt") or ""
        first = cfg.get("first_sentence", "")
        tools = {t.get("name") for t in cfg.get("tools", [])}
        if cfg.get("transfer_phone_number"):
            tools.add("transfer_to_human")
    tools.discard(None)
    meta = cfg.get("metadata") or {}
    return Doc(prompt=prompt, first_message=first, tools=tools,
               price_policy=meta.get("price_policy", "never"),
               recording_rule=meta.get("recording_rule", "two_party"),
               trade=meta.get("trade", ""), source=source)


def load_doc(path, **overrides) -> Doc:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        doc = doc_from_config(json.loads(text), str(p))
    else:
        doc = Doc(prompt=text, source=str(p))
    for k, v in overrides.items():
        if v is not None:
            setattr(doc, k, v)
    return doc


def lint(doc: Doc, only: list[str] | None = None, skip: list[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for r in RULES:
        if only and r.id not in only:
            continue
        if skip and r.id in skip:
            continue
        findings.extend(r.fn(doc))
    return findings


__all__ = ["lint", "load_doc", "doc_from_config", "detect_platform", "Doc", "Finding", "RULES", "RULE_BY_ID", "DEFAULT_MAX_CHARS"]
