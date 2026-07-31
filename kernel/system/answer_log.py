"""Rotating markdown answer log.

Interactive terminals in this environment are sometimes heavily truncated or
otherwise limited, so both the engine's own CLI output and answers given about
the engine are additionally persisted to disk as plain markdown that can be
opened in any editor. Only the current and previous answer are kept — this is
a scratch surface for "what just happened", not an audit log (the ledger
already covers that).
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

ANSWER_FILE = "answer.md"
PREVIOUS_ANSWER_FILE = "previous_answer.md"

# User-facing timestamps are always shown in GMT+2, regardless of the host
# system's local timezone — fixed offset (not a zoneinfo name) so this has no
# external dependency and needs no DST database.
DISPLAY_TZ = timezone(timedelta(hours=2))


def write_answer(root: Path, content: str) -> None:
    """Rotate answer.md -> previous_answer.md, then write new content to answer.md.

    A timestamp footer is always appended so it's clear, without checking file
    metadata, exactly when an answer was produced — important once there's a
    rotated previous_answer.md sitting next to it.
    """
    root = Path(root)
    answer_path = root / ANSWER_FILE
    previous_path = root / PREVIOUS_ANSWER_FILE

    if answer_path.exists():
        previous_path.write_text(answer_path.read_text(encoding="utf-8"), encoding="utf-8")

    timestamp = datetime.now(DISPLAY_TZ).strftime("%Y-%m-%d %H:%M:%S %z")
    stamped_content = content.rstrip("\n") + f"\n\n---\n_Generálva: {timestamp}_\n"
    answer_path.write_text(stamped_content, encoding="utf-8")
