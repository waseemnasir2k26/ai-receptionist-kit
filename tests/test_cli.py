import json
from pathlib import Path

from kit.cli import main
from kit.lint import doc_from_config, lint

ROOT = Path(__file__).resolve().parent.parent


def test_init_build_lint_roundtrip(tmp_path):
    biz = tmp_path / "business.json"
    assert main(["init", "--preset", "hvac", "--name", "Acme Air", "--out", str(biz)]) == 0
    assert json.loads(biz.read_text(encoding="utf-8"))["business_name"] == "Acme Air"
    out = tmp_path / "dist"
    assert main(["build", str(biz), "--platform", "all", "--out", str(out)]) == 0
    for platform in ("vapi", "retell", "bland"):
        for name in ("assistant.json", "prompt.md", "tools.json"):
            assert (out / platform / name).is_file()
        cfg = json.loads((out / platform / "assistant.json").read_text(encoding="utf-8"))
        assert lint(doc_from_config(cfg)) == []
    assert main(["lint", str(out / "vapi" / "prompt.md")]) == 0


def test_build_single_platform(tmp_path):
    biz = tmp_path / "b.json"
    main(["init", "--preset", "roofer", "--out", str(biz)])
    out = tmp_path / "dist"
    assert main(["build", str(biz), "--platform", "retell", "--out", str(out)]) == 0
    assert [p.name for p in out.iterdir()] == ["retell"]


def test_init_refuses_overwrite(tmp_path):
    biz = tmp_path / "b.json"
    assert main(["init", "--preset", "plumber", "--out", str(biz)]) == 0
    assert main(["init", "--preset", "plumber", "--out", str(biz)]) == 2
    assert main(["init", "--preset", "plumber", "--out", str(biz), "--force"]) == 0


def test_example_custom_intake_builds_and_lints(tmp_path):
    biz = ROOT / "examples" / "business-hvac-bilingual.json"
    assert main(["validate", str(biz)]) == 0
    out = tmp_path / "d"
    assert main(["build", str(biz), "--out", str(out)]) == 0
    prompt = (out / "vapi" / "prompt.md").read_text(encoding="utf-8")
    assert "Spanish" in prompt and "Drain" not in prompt
    cfg = json.loads((out / "vapi" / "assistant.json").read_text(encoding="utf-8"))
    assert cfg["transcriber"]["language"] == "multi"
    assert lint(doc_from_config(cfg)) == []


def test_ranges_policy_prompt(tmp_path):
    biz = ROOT / "examples" / "business-hvac-bilingual.json"
    data = json.loads(biz.read_text(encoding="utf-8"))
    assert data["price_policy"] == "ranges"
    out = tmp_path / "d"
    main(["build", str(biz), "--out", str(out)])
    prompt = (out / "vapi" / "prompt.md").read_text(encoding="utf-8")
    assert "Never give an exact quote" in prompt
    assert data["price_ranges"][0] in prompt


def test_presets_command(capsys):
    assert main(["presets"]) == 0
    out = capsys.readouterr().out
    for name in ("plumber", "hvac", "electrician", "dental", "cleaning", "roofer"):
        assert name in out


def test_callback_booking_prompt_mentions_no_direct_booking(tmp_path):
    biz = tmp_path / "b.json"
    main(["init", "--preset", "cleaning", "--out", str(biz)])
    data = json.loads(biz.read_text(encoding="utf-8"))
    data["booking"] = {"method": "callback"}
    biz.write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "d"
    assert main(["build", str(biz), "--platform", "vapi", "--out", str(out)]) == 0
    prompt = (out / "vapi" / "prompt.md").read_text(encoding="utf-8")
    assert "You cannot book directly" in prompt


def test_no_secrets_or_real_numbers_in_generated_files():
    for p in (ROOT / "examples" / "dist-plumber").rglob("*.json"):
        text = p.read_text(encoding="utf-8")
        assert "+15555550100" in text or "transfer" not in p.name
        assert "sk-" not in text and "api_key" not in text.lower()
