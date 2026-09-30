"""The demo must not reach the network, in anything the browser loads.

CI's shell guard only scanned dashboard/*.py; the templates and the compiled
stylesheet are what the browser actually loads (pre-production test, 30 Sept).
A URL inside a CSS/JS comment is not fetched (the Tailwind licence line), so
comments are stripped before scanning; anything else fails.
"""
import re
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard"
SERVED = {".py", ".jinja", ".html", ".css", ".js"}
COMMENT = re.compile(r"/\*.*?\*/", re.S)
URL = re.compile(r"https?://")


def test_nothing_the_dashboard_serves_references_the_network():
    offenders = []
    for path in DASHBOARD.rglob("*"):
        if path.suffix not in SERVED or "node_modules" in path.parts or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix in {".css", ".js"}:
            text = COMMENT.sub("", text)
        offenders += [f"{path.relative_to(DASHBOARD)}:{text[:m.start()].count(chr(10)) + 1}"
                      for m in URL.finditer(text)]
    assert not offenders, offenders
