"""The test counts quoted in `CONTEXT.md` §4.

That section tells a new session what a good state looks like and says
"anything less is a regression, not a quirk". A stale count there is worse
than no count, because it trains the reader to ignore the mismatch the line
exists to catch. It went stale twice: 249 -> 253 as tests were added, and a
placeholder count that read 24 against a suite reporting 25.

So the numbers are **generated, not asserted**. This module collects the suite
and reads CONTEXT.md, then compares. Nothing here hardcodes an expected total,
which means adding a test cannot make this file wrong - it can only make
CONTEXT.md wrong, which is the thing worth detecting.

Collection runs in a subprocess with `--collect-only`, so no test executes
twice and this stays fast.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTEXT = REPO_ROOT / "CONTEXT.md"

SELECTED = re.compile(r"(\d+)/(\d+) tests collected \((\d+) deselected\)")
NO_DESELECTION = re.compile(r"(\d+) tests collected")


def _collected(marker_expression: str) -> tuple[int, int]:
    """Return (selected, deselected) for a marker expression, by collecting it."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            marker_expression,
            "-q",
            "--collect-only",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr

    match = SELECTED.search(output)
    if match:
        return int(match.group(1)), int(match.group(3))

    match = NO_DESELECTION.search(output)
    if match:
        return int(match.group(1)), 0

    pytest.fail(f"could not parse collection output for -m {marker_expression!r}:\n{output}")


def _quoted(pattern: str) -> tuple[int, ...]:
    text = CONTEXT.read_text(encoding="utf-8")
    match = re.search(pattern, text)
    if match is None:
        pytest.fail(f"CONTEXT.md no longer contains the line matching {pattern!r}")
    return tuple(int(g) for g in match.groups())


def test_context_quotes_the_real_passing_and_deselected_counts() -> None:
    """§4's "Expect N passed, M deselected" must match what the suite collects."""
    selected, deselected = _collected("not placeholder")
    quoted_passed, quoted_deselected = _quoted(r"Expect \*\*(\d+) passed, (\d+) deselected\*\*")

    assert (quoted_passed, quoted_deselected) == (selected, deselected), (
        f"CONTEXT.md §4 says {quoted_passed} passed / {quoted_deselected} deselected; "
        f"the suite collects {selected} / {deselected}. Update CONTEXT.md."
    )


def test_context_quotes_the_real_placeholder_count() -> None:
    """§4's "Expect N failed" must match the number of placeholder tests."""
    placeholders, _ = _collected("placeholder")
    (quoted_failing,) = _quoted(r"Expect \*\*(\d+) failed\*\*")

    assert quoted_failing == placeholders, (
        f"CONTEXT.md §4 says {quoted_failing} placeholder failures; "
        f"the suite collects {placeholders}. Update CONTEXT.md."
    )


def test_the_two_counts_partition_the_whole_suite() -> None:
    """Cross-check: selected + deselected is the same total from either side.

    This is what makes the pair trustworthy rather than two numbers that
    happen to be individually right.
    """
    selected, deselected = _collected("not placeholder")
    placeholders, placeholder_deselected = _collected("placeholder")

    assert selected + deselected == placeholders + placeholder_deselected
    assert deselected == placeholders, (
        "everything deselected by 'not placeholder' should be a placeholder test"
    )
