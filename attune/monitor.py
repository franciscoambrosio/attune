"""
State management for attune watch mode.

State file: ~/.attune/state.json
  last_checked_ts  — Unix timestamp of the last successful poll
  seen_ids         — capped list of already-triaged email IDs (dedup safety net)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path.home() / ".attune" / "state.json"
MAX_SEEN   = 1000


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    # First run: start from now so we only triage future mail
    return {
        "last_checked_ts": int(datetime.now(timezone.utc).timestamp()),
        "seen_ids": [],
    }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def update_state(state: dict, new_ids: list[str]) -> dict:
    state["last_checked_ts"] = int(datetime.now(timezone.utc).timestamp())
    seen = state["seen_ids"] + new_ids
    state["seen_ids"] = seen[-MAX_SEEN:]
    return state
