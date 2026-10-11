import json
import shutil
import subprocess
from pathlib import Path

import pytest

from kit.cli import main
from kit.n8n_validate import validate_workflow
from kit.responder import respond

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / "n8n" / "booking-webhook.json"

VAPI_PAYLOAD = {"message": {"type": "tool-calls", "toolCallList": [
    {"id": "call_1", "name": "check_availability", "arguments": {"service_type": "drain cleaning"}},
    {"id": "call_2", "name": "book_appointment", "arguments": {"customer_name": "Sam"}},
    {"id": "call_3", "name": "log_lead", "arguments": {}}]}}


def test_result_shape_vapi_list():
    out = respond(VAPI_PAYLOAD)
    assert list(out) == ["results"]
    assert [r["toolCallId"] for r in out["results"]] == ["call_1", "call_2", "call_3"]
    for r in out["results"]:
        assert set(r) == {"toolCallId", "result"}
        assert isinstance(r["result"], str) and "\n" not in r["result"]


def test_result_shape_openai_style_with_json_string_args():
    payload = {"body": {"message": {"toolCalls": [
        {"id": "x1", "type": "function", "function": {"name": "book_appointment", "arguments": "{\"customer_name\": \"Ana\"}"}}]}}}
    out = respond(payload)
    assert out["results"][0]["toolCallId"] == "x1"
    assert "Ana" in out["results"][0]["result"]


def test_bad_arguments_and_unknown_tool_do_not_crash():
    payload = {"message": {"toolCallList": [
        {"id": "a", "name": "check_availability", "arguments": "{not json"},
        {"id": "b", "name": "mystery", "arguments": {}},
        {"name": "no_id", "arguments": {}}]}}
    out = respond(payload)
    assert [r["toolCallId"] for r in out["results"]] == ["a", "b"]
    assert out["results"][1]["result"] == "Unknown tool: mystery"


def test_empty_payload_returns_empty_results():
    assert respond({}) == {"results": []}
    assert respond({"message": {"type": "status-update"}}) == {"results": []}


def test_every_generated_tool_is_handled():
    tools = json.loads((ROOT / "examples" / "dist-plumber" / "vapi" / "tools.json").read_text(encoding="utf-8"))
    for t in tools:
        out = respond({"message": {"toolCallList": [{"id": "i", "name": t["name"], "arguments": {}}]}})
        assert not out["results"][0]["result"].startswith("Unknown tool")


def test_workflow_file_is_valid():
    wf = json.loads(WF.read_text(encoding="utf-8"))
    assert validate_workflow(wf) == []
    assert main(["validate-n8n", str(WF)]) == 0


def test_workflow_embeds_current_handler_js():
    wf = json.loads(WF.read_text(encoding="utf-8"))
    code = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.code")
    assert code["parameters"]["jsCode"] == (ROOT / "n8n" / "handler.js").read_text(encoding="utf-8")


def test_validator_catches_breakage():
    wf = json.loads(WF.read_text(encoding="utf-8"))
    broken = json.loads(json.dumps(wf))
    broken["nodes"] = [n for n in broken["nodes"] if n["type"] != "n8n-nodes-base.respondToWebhook"]
    assert any("respondToWebhook" in e for e in validate_workflow(broken))
    broken = json.loads(json.dumps(wf))
    broken["nodes"][0]["parameters"]["responseMode"] = "onReceived"
    assert any("responseMode" in e for e in validate_workflow(broken))
    broken = json.loads(json.dumps(wf))
    broken["connections"] = {}
    assert len(validate_workflow(broken)) == 2
    assert validate_workflow([]) == ["workflow must be a JSON object"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_handler_matches_python_reference(tmp_path):
    js = (ROOT / "n8n" / "handler.js").read_text(encoding="utf-8")
    runner = tmp_path / "run.js"
    runner.write_text(
        "const fn = new Function('$input', " + json.dumps(js) + ");\n"
        "const payload = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));\n"
        "const out = fn({ first: () => ({ json: { body: payload } }) });\n"
        "console.log(JSON.stringify(out[0].json));\n", encoding="utf-8")
    payloads = [VAPI_PAYLOAD,
                {"message": {"toolCalls": [{"id": "x1", "function": {"name": "book_appointment", "arguments": "{\"customer_name\": \"Ana\"}"}}]}},
                {"message": {"toolCallList": [{"id": "b", "name": "mystery", "arguments": {}}]}},
                {}]
    for i, payload in enumerate(payloads):
        pf = tmp_path / f"p{i}.json"
        pf.write_text(json.dumps(payload), encoding="utf-8")
        got = json.loads(subprocess.run(["node", str(runner), str(pf)], capture_output=True, text=True, check=True).stdout)
        assert got == respond(payload)
