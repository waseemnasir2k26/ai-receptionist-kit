import copy
import json

import pytest

from kit import intake
from kit.cli import main


@pytest.fixture
def good():
    return intake.from_preset("plumber")


def errs(data):
    return intake.validate(data)


@pytest.mark.parametrize("preset", intake.list_presets())
def test_every_preset_intake_is_valid(preset):
    assert errs(intake.from_preset(preset)) == []


def test_non_object():
    assert errs([]) == ["$: intake must be a JSON object"]


def test_unknown_key_is_reported(good):
    good["bussiness_name"] = "typo"
    assert any(e.startswith("bussiness_name: unknown key") for e in errs(good))


def test_bad_trade(good):
    good["trade"] = "astronaut"
    assert any(e.startswith("trade:") for e in errs(good))


def test_missing_business_name(good):
    del good["business_name"]
    assert any(e.startswith("business_name:") for e in errs(good))


def test_bad_timezone(good):
    good["hours"]["timezone"] = "Chicago time"
    assert any(e.startswith("hours.timezone") for e in errs(good))


def test_bad_hours_range(good):
    good["hours"]["weekly"]["mon"] = "17:00-08:00"
    assert any("opening time must be before closing" in e for e in errs(good))
    good["hours"]["weekly"]["mon"] = "8am-5pm"
    assert any(e.startswith("hours.weekly.mon") for e in errs(good))


def test_weekly_missing_day(good):
    del good["hours"]["weekly"]["sun"]
    assert any(e.startswith("hours.weekly: must have exactly") for e in errs(good))


def test_all_days_closed(good):
    good["hours"]["weekly"] = {d: None for d in intake.DAYS}
    assert any("at least one day must be open" in e for e in errs(good))


def test_zip_required_except_dental(good):
    good["service_area_zips"] = []
    assert any(e.startswith("service_area_zips") for e in errs(good))
    d = intake.from_preset("dental")
    assert errs(d) == []


def test_empty_emergency_keywords(good):
    good["emergency"]["keywords"] = []
    assert any(e.startswith("emergency.keywords") for e in errs(good))


def test_price_policy_values_and_ranges_requirement(good):
    good["price_policy"] = "sometimes"
    assert any(e.startswith("price_policy") for e in errs(good))
    good["price_policy"] = "ranges"
    assert any(e.startswith("price_ranges") for e in errs(good))
    good["price_ranges"] = ["Drain cleaning: $150 to $300"]
    assert errs(good) == []


def test_webhook_must_be_https(good):
    good["booking"]["webhook_url"] = "http://example.com/x"
    assert any(e.startswith("booking.webhook_url") for e in errs(good))
    good["booking"] = {"method": "callback"}
    assert errs(good) == []


def test_transfer_number_must_be_e164(good):
    good["transfer_number"] = "555-0100"
    assert any(e.startswith("transfer_number") for e in errs(good))


def test_recording_consent_rules(good):
    good["recording_consent"] = {"region": "US-CA", "rule": "maybe"}
    assert any(e.startswith("recording_consent.rule") for e in errs(good))
    good["recording_consent"] = {"rule": "two_party"}
    assert any(e.startswith("recording_consent.region") for e in errs(good))


def test_languages(good):
    good["languages"] = ["english"]
    assert any(e.startswith("languages") for e in errs(good))
    good["languages"] = ["es"]
    assert any("include 'en'" in e for e in errs(good))
    good["languages"] = ["en", "es"]
    assert errs(good) == []


def test_faq_shape(good):
    good["faqs"] = [{"q": "only a question"}]
    assert any(e.startswith("faqs") for e in errs(good))


def test_multiple_errors_reported_together(good):
    good["transfer_number"] = "x"
    good["price_policy"] = "x"
    good["agent_name"] = ""
    assert len(errs(good)) >= 3


def test_load_rejects_bad_json(tmp_path):
    p = tmp_path / "b.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(intake.IntakeError) as exc:
        intake.load(p)
    assert "invalid JSON" in str(exc.value)


def test_build_refuses_invalid_intake(tmp_path, capsys):
    data = copy.deepcopy(intake.from_preset("plumber"))
    data["transfer_number"] = "nope"
    p = tmp_path / "b.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert main(["build", str(p), "--out", str(tmp_path / "d")]) == 2
    assert not (tmp_path / "d").exists()
    assert "transfer_number" in capsys.readouterr().err


def test_validate_command(tmp_path, capsys):
    p = tmp_path / "b.json"
    p.write_text(json.dumps(intake.from_preset("roofer")), encoding="utf-8")
    assert main(["validate", str(p)]) == 0
    p.write_text(json.dumps({"trade": "roofer"}), encoding="utf-8")
    assert main(["validate", str(p)]) == 1
    assert "INVALID" in capsys.readouterr().out
