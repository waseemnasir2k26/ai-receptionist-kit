import json
from pathlib import Path

import pytest

from kit import intake
from kit.cli import dumps
from kit.render import PLATFORMS, render

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden"
PRESETS = intake.list_presets()


def test_six_presets_exist():
    assert PRESETS == ["cleaning", "dental", "electrician", "hvac", "plumber", "roofer"]


@pytest.mark.parametrize("platform", list(PLATFORMS))
@pytest.mark.parametrize("preset", PRESETS)
def test_golden_output(preset, platform):
    out = dumps(render(platform, intake.from_preset(preset)))
    expected = (GOLDEN / f"{preset}-{platform}.json").read_text(encoding="utf-8")
    assert out == expected, "output changed; if intended run: python tests/regen_golden.py"


@pytest.mark.parametrize("preset", PRESETS)
def test_deterministic(preset):
    a = dumps(render("vapi", intake.from_preset(preset)))
    b = dumps(render("vapi", intake.from_preset(preset)))
    assert a == b


@pytest.mark.parametrize("platform", list(PLATFORMS))
def test_metadata_built_with(platform):
    cfg = render(platform, intake.from_preset("hvac"))
    assert cfg["metadata"]["built_with"] == "ai-receptionist-kit (SkynetLabs)"
    assert cfg["metadata"]["trade"] == "hvac"
    assert "timestamp" not in json.dumps(cfg).lower()


def test_example_dist_is_current():
    base = ROOT / "examples" / "dist-plumber"
    for platform in PLATFORMS:
        expected = dumps(render(platform, intake.from_preset("plumber")))
        assert (base / platform / "assistant.json").read_text(encoding="utf-8") == expected
    assert json.loads((base / "business.json").read_text(encoding="utf-8")) == intake.from_preset("plumber")


def test_emergency_keywords_reach_prompt():
    for preset in PRESETS:
        data = intake.from_preset(preset)
        text = render("vapi", data)["model"]["messages"][0]["content"]
        for kw in data["emergency"]["keywords"]:
            assert kw in text
    hvac = intake.from_preset("hvac")
    assert any("under 40 degrees" in k for k in hvac["emergency"]["keywords"])


def test_platform_shapes():
    data = intake.from_preset("plumber")
    v = render("vapi", data)
    names = [t["function"]["name"] for t in v["model"]["tools"]]
    assert names == ["check_availability", "book_appointment", "transfer_to_human", "log_lead"]
    assert v["model"]["tools"][2]["type"] == "transferCall"
    assert v["model"]["tools"][2]["destinations"][0]["number"] == data["transfer_number"]
    r = render("retell", data)
    assert {t["name"] for t in r["llm"]["general_tools"]} == {"check_availability", "book_appointment", "transfer_to_human", "log_lead", "end_call"}
    assert r["agent"]["response_engine"]["type"] == "retell-llm"
    b = render("bland", data)
    assert b["transfer_phone_number"] == data["transfer_number"]
    assert [t["name"] for t in b["tools"]] == ["check_availability", "book_appointment", "log_lead"]


def test_dental_has_no_address_and_has_guardrail():
    data = intake.from_preset("dental")
    cfg = render("vapi", data)
    book = cfg["model"]["tools"][1]["function"]["parameters"]
    assert "service_address" not in book["properties"]
    assert "patient_status" in book["properties"]
    assert "Do not give medical or dental advice" in cfg["model"]["messages"][0]["content"]


def test_recording_none_disables_recording():
    data = intake.from_preset("plumber")
    data["recording_consent"] = {"region": "n/a", "rule": "none"}
    assert render("vapi", data)["recordingEnabled"] is False
    assert render("bland", data)["record"] is False
    assert "recorded" not in render("vapi", data)["firstMessage"]
