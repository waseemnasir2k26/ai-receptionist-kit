"""Regenerate tests/golden/*.json and examples/dist-plumber from the current renderers.

Run after an intentional change to templates, presets or renderers, review the diff, commit.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit import intake  # noqa: E402
from kit.cli import build_all, dumps  # noqa: E402
from kit.render import PLATFORMS, render  # noqa: E402

golden = ROOT / "tests" / "golden"
golden.mkdir(exist_ok=True)
for preset in intake.list_presets():
    data = intake.from_preset(preset)
    for platform in PLATFORMS:
        (golden / f"{preset}-{platform}.json").write_text(dumps(render(platform, data)), encoding="utf-8", newline="\n")

example = ROOT / "examples" / "dist-plumber"
example.mkdir(parents=True, exist_ok=True)
(example / "business.json").write_text(dumps(intake.from_preset("plumber")), encoding="utf-8", newline="\n")
build_all(intake.from_preset("plumber"), "all", example)
print("golden + examples/dist-plumber regenerated")
