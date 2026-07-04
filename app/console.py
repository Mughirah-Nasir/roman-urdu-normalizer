"""
Console output helpers shared by the CLI, benchmark harness, and scripts.

Windows consoles frequently default to a legacy code page (cp1252 / cp437)
that cannot encode the box-drawing characters and Roman Urdu pass-through
text (emoji, Nastaliq) these tools print. Without this fix, every benchmark
and report script dies with UnicodeEncodeError on a stock Windows terminal —
ironic for a tool aimed at Pakistan, where Windows dominates.
"""

from __future__ import annotations

import sys


def ensure_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 so report output never crashes on
    legacy Windows code pages. Call once at the top of any console entry
    point that prints non-ASCII (box-drawing chars, user text, emoji).

    Safe no-op when the stream does not support reconfigure (e.g. some
    captured/redirected streams) — those already accept arbitrary text.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - stream closed/detached
            pass
