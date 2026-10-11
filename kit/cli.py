"""Command line: init, build, lint, validate, validate-n8n, presets."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, intake as intake_mod
from .lint import DEFAULT_MAX_CHARS, RULES, lint, load_doc
from .n8n_validate import validate_file
from .render import PLATFORMS, common, render


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def build_all(intake: dict, platform: str, out: Path) -> list[Path]:
    """Write <out>/<platform>/{assistant.json,prompt.md,tools.json}. Returns the paths written."""
    names = list(PLATFORMS) if platform == "all" else [platform]
    written = []
    for name in names:
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        files = {
            "assistant.json": dumps(render(name, intake)),
            "prompt.md": common.prompt(intake),
            "tools.json": dumps(common.tools(intake)),
        }
        for fname, text in files.items():
            (d / fname).write_text(text, encoding="utf-8", newline="\n")
            written.append(d / fname)
    return written


def cmd_init(a) -> int:
    out = Path(a.out)
    if out.exists() and not a.force:
        print(f"error: {out} already exists (use --force to overwrite)", file=sys.stderr)
        return 2
    try:
        data = intake_mod.from_preset(a.preset, a.name)
    except intake_mod.IntakeError as exc:
        print("error: " + "; ".join(exc.errors), file=sys.stderr)
        return 2
    out.write_text(dumps(data), encoding="utf-8", newline="\n")
    print(f"wrote {out} from preset '{a.preset}'. Edit it, then: ai-receptionist-kit build {out} --platform all --out dist/")
    return 0


def cmd_build(a) -> int:
    try:
        data = intake_mod.load(a.intake)
    except intake_mod.IntakeError as exc:
        print(f"{a.intake}: invalid intake", file=sys.stderr)
        for line in exc.errors:
            print(f"  - {line}", file=sys.stderr)
        return 2
    written = build_all(data, a.platform, Path(a.out))
    for p in written:
        print(f"wrote {p}")
    print("\nNext: set the voice id, confirm the webhook URL and transfer number, run the lint, test with a call to your own phone.")
    print("Nothing was deployed or called. Platform schemas change: see docs/platforms.md.")
    return 0


def cmd_lint(a) -> int:
    only = a.only.split(",") if a.only else None
    skip = a.skip.split(",") if a.skip else None
    total = {"error": 0, "warn": 0}
    report = []
    tools_override = None
    if a.tools:
        raw = json.loads(Path(a.tools).read_text(encoding="utf-8"))
        tools_override = {t.get("name") or (t.get("function") or {}).get("name") for t in raw}
    for path in a.paths:
        try:
            doc = load_doc(path, price_policy=a.price_policy, recording_rule=a.recording_rule, trade=a.trade,
                           max_chars=a.max_chars, tools=tools_override)
        except (OSError, ValueError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2
        findings = lint(doc, only, skip)
        for f in findings:
            total[f.severity] += 1
        report.append((path, doc, findings))
    if a.format == "json":
        print(json.dumps([{"file": str(p), "tools_checked": d.tools is not None, "findings": [f.__dict__ for f in fs]}
                          for p, d, fs in report], indent=2))
    else:
        for path, doc, findings in report:
            print(path)
            if not findings:
                print("  clean")
            for f in findings:
                loc = f" (line {f.line})" if f.line else ""
                print(f"  {f.rule} {f.severity:<5} {f.message}{loc}")
            if doc.tools is None:
                print("  note: RCP008 skipped (prompt-only input, no tool schemas; pass --tools tools.json)")
        n_rules = len([r for r in RULES if (not only or r.id in only) and (not skip or r.id not in skip)])
        print(f"\n{n_rules} rules checked: {total['error']} error(s), {total['warn']} warning(s)")
    if total["error"]:
        return 1
    if total["warn"] and a.fail_on == "warn":
        return 1
    return 0


def cmd_validate(a) -> int:
    try:
        intake_mod.load(a.intake)
    except intake_mod.IntakeError as exc:
        print(f"{a.intake}: INVALID")
        for line in exc.errors:
            print(f"  - {line}")
        return 1
    print(f"{a.intake}: ok")
    return 0


def cmd_validate_n8n(a) -> int:
    errs = validate_file(a.workflow)
    if errs:
        print(f"{a.workflow}: INVALID")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"{a.workflow}: ok")
    return 0


def cmd_presets(a) -> int:
    for name in intake_mod.list_presets():
        p = intake_mod.load_preset(name)
        print(f"{name:<12} {p['description']}")
    return 0


def make_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ai-receptionist-kit", description="Generate and lint AI voice receptionist configs (Vapi, Retell, Bland). Offline.")
    ap.add_argument("--version", action="version", version=f"ai-receptionist-kit {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write a starter business.json from a trade preset")
    s.add_argument("--preset", required=True, choices=intake_mod.list_presets() or None)
    s.add_argument("--name", help="business name")
    s.add_argument("--out", default="business.json")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("build", help="render assistant JSON, prompt and tool schemas")
    s.add_argument("intake")
    s.add_argument("--platform", choices=[*PLATFORMS, "all"], default="all")
    s.add_argument("--out", default="dist")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("lint", help="lint a prompt (.md/.txt) or a rendered platform config (.json)")
    s.add_argument("paths", nargs="+")
    s.add_argument("--format", choices=["text", "json"], default="text")
    s.add_argument("--fail-on", choices=["error", "warn"], default="error")
    s.add_argument("--price-policy", choices=list(intake_mod.PRICE_POLICIES))
    s.add_argument("--recording-rule", choices=list(intake_mod.CONSENT_RULES))
    s.add_argument("--trade", help="e.g. dental enables RCP012")
    s.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    s.add_argument("--tools", help="JSON list of tool schemas (enables RCP008 for prompt-only input)")
    s.add_argument("--only", help="comma-separated rule ids")
    s.add_argument("--skip", help="comma-separated rule ids")
    s.set_defaults(fn=cmd_lint)

    s = sub.add_parser("validate", help="validate a business.json intake")
    s.add_argument("intake")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("validate-n8n", help="structurally validate the n8n responder workflow JSON")
    s.add_argument("workflow")
    s.set_defaults(fn=cmd_validate_n8n)

    s = sub.add_parser("presets", help="list trade presets")
    s.set_defaults(fn=cmd_presets)
    return ap


def main(argv=None) -> int:
    a = make_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
