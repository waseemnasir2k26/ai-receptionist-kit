"""Render the REAL lint output for examples/bad-prompt.md to docs/lint-report.svg.

The text is captured from the CLI at run time, not typed by hand.
"""
import contextlib
import io
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.cli import main  # noqa: E402

cmd = ["lint", "examples/bad-prompt.md", "--tools", "examples/dist-plumber/vapi/tools.json"]
buf = io.StringIO()
import os  # noqa: E402

os.chdir(ROOT)
with contextlib.redirect_stdout(buf):
    code = main(cmd)

lines = ["$ ai-receptionist-kit " + " ".join(cmd)] + buf.getvalue().rstrip("\n").splitlines() + [f"(exit code {code})"]
# keep lines readable: wrap at 118 chars
wrapped = []
for ln in lines:
    while len(ln) > 118:
        cut = ln.rfind(" ", 0, 118)
        cut = cut if cut > 60 else 118
        wrapped.append(ln[:cut])
        ln = "      " + ln[cut:].lstrip()
    wrapped.append(ln)

lh, pad, cw = 20, 20, 8.4
width = int(max(len(x) for x in wrapped) * cw + pad * 2)
height = len(wrapped) * lh + pad * 2 + 28
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="ai-receptionist-kit lint report">',
       f'<rect width="{width}" height="{height}" rx="10" fill="#0f172a"/>',
       '<circle cx="22" cy="18" r="6" fill="#ef4444"/><circle cx="42" cy="18" r="6" fill="#f59e0b"/><circle cx="62" cy="18" r="6" fill="#22c55e"/>',
       '<g font-family="Consolas, Menlo, monospace" font-size="14">']
y = 28 + pad + 10
for ln in wrapped:
    color = "#e2e8f0"
    if ln.startswith("$"):
        color = "#94a3b8"
    elif " error " in ln:
        color = "#fca5a5"
    elif " warn  " in ln:
        color = "#fcd34d"
    elif "rules checked" in ln:
        color = "#86efac"
    out.append(f'<text x="{pad}" y="{y}" fill="{color}" xml:space="preserve">{escape(ln)}</text>')
    y += lh
out.append("</g></svg>")
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "lint-report.svg").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote docs/lint-report.svg", width, height)
